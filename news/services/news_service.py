import json
import os
import re
import urllib.parse

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils.text import slugify

from news.models import News


def create_news(
    *,
    title: str,
    thumbnail_image=None,
    thumbnail_alt_description: str = None,
    content: str = None,
    url: str = None,
    meta_title: str = None,
    meta_description: str = None,
) -> News:
    with transaction.atomic():
        news = News(
            title=title,
            thumbnail_image=thumbnail_image,
            thumbnail_alt_description=thumbnail_alt_description,
            content=content,
            url=url,
            meta_title=meta_title,
            meta_description=meta_description,
        )
        news.full_clean()
        news.save()
        return news


def update_news(*, news: News, **data) -> News:
    with transaction.atomic():
        for field, value in data.items():
            setattr(news, field, value)
        news.full_clean()
        news.save()
        return news


def resolve_image_file(attachment):
    """
    Given an attachment dict from attachments.json, find the actual file
    on disk in the flat media/ directory (checking both plain and prefixed names).
    """
    rel_path = attachment.get("postmeta", {}).get("_wp_attached_file")
    if not rel_path:
        url = attachment.get("attachment_url") or attachment.get("guid", "")
        parsed_url = urllib.parse.urlparse(url)
        rel_path = os.path.basename(parsed_url.path)

    if isinstance(rel_path, list):
        rel_path = rel_path[0]

    basename = os.path.basename(rel_path)
    dir_part = os.path.dirname(rel_path)
    prefix = dir_part.replace("/", "_").replace("\\", "_") if dir_part else ""

    media_dir = os.path.join(settings.BASE_DIR, "media")

    # 1. Check plain basename (e.g. Rethinking.jpg)
    path_plain = os.path.join(media_dir, basename)
    if os.path.exists(path_plain):
        return path_plain

    # 2. Check prefixed version (e.g. 2020_11_Rethinking.jpg)
    if prefix:
        path_prefixed = os.path.join(media_dir, f"{prefix}_{basename}")
        if os.path.exists(path_prefixed):
            return path_prefixed

    return None


def parse_news_content(content, attachments_map):
    """
    Parse visual composer shortcodes from the page content to extract news articles.
    """
    columns = re.findall(r"\[vc_column.*?\](.*?)\[/vc_column\]", content, re.DOTALL)
    news_items = []
    for col in columns:
        # Extract image ID
        image_match = re.search(r'vc_single_image\s+[^\]]*image=["\'](\d+)["\']', col)
        image_id = int(image_match.group(1)) if image_match else None

        # Extract main link from vc_single_image link
        link_match = re.search(r'vc_single_image\s+[^\]]*link=["\']([^"\']+)["\']', col)
        main_link = link_match.group(1) if link_match else None
        if not main_link:
            # Fallback to the first anchor tag's href
            a_match = re.search(r'<a\s+[^>]*href=["\']([^"\']+)["\']', col)
            main_link = a_match.group(1) if a_match else None

        # Extract Title: text inside h3/h4/h5 tags or fallback to attachment title
        title_match = re.search(r"<h3[^>]*>(.*?)</h3>", col, re.DOTALL) or \
                      re.search(r"<h4[^>]*>(.*?)</h4>", col, re.DOTALL) or \
                      re.search(r"<h5[^>]*>(.*?)</h5>", col, re.DOTALL)
        if title_match:
            title = re.sub(r"<[^>]+>", "", title_match.group(1))
        else:
            if image_id and image_id in attachments_map:
                title = attachments_map[image_id].get("title") or ""
            else:
                title = ""

        title = title.replace("&nbsp;", " ").replace("&#160;", " ").strip()

        # Extract Content/Author (if any paragraphs or divs exist)
        text_blocks = re.findall(r"<p[^>]*>(.*?)</p>", col, re.DOTALL) or \
                      re.findall(r"<div[^>]*>(.*?)</div>", col, re.DOTALL)
        content_text = ""
        for block in text_blocks:
            cleaned = re.sub(r"<[^>]+>", "", block).strip()
            if cleaned and cleaned not in title:
                content_text = cleaned
                break

        if main_link:
            if not title:
                parsed_url = urllib.parse.urlparse(main_link)
                title = os.path.basename(parsed_url.path).replace("-", " ").replace("_", " ").title()
                if not title or title == ".html":
                    title = "News Item"

            news_items.append({
                "title": title,
                "image_id": image_id,
                "main_link": main_link,
                "content": content_text
            })
    return news_items


def import_news() -> dict:
    """
    Imports News from pages.json (post_id: 1409 or slug news-and-features)
    and links the document/URL and thumbnail files.
    """
    pages_path = os.path.join(settings.BASE_DIR, "pages.json")
    attachments_path = os.path.join(settings.BASE_DIR, "attachments.json")

    if not os.path.exists(pages_path):
        raise FileNotFoundError(f"pages.json not found at {pages_path}")

    # Load pages
    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    # Find the News and Features page
    target_page = None
    for page in pages:
        if page.get("post_id") == 1409 or page.get("slug") == "news-and-features":
            target_page = page
            break

    if not target_page:
        raise ValueError("News and Features page not found in pages.json")

    content = target_page.get("content") or ""
    if not content:
        raise ValueError("News and Features page content is empty")

    # Load attachments to resolve image IDs
    attachments_map = {}
    if os.path.exists(attachments_path):
        with open(attachments_path, "r", encoding="utf-8") as f:
            attachments = json.load(f)
            for att in attachments:
                post_id = att.get("post_id")
                if post_id:
                    attachments_map[post_id] = att

    parsed_news = parse_news_content(content, attachments_map)
    imported_count = 0

    with transaction.atomic():
        for news_data in parsed_news:
            title = news_data["title"]
            main_link = news_data["main_link"]
            image_id = news_data["image_id"]
            news_content = news_data["content"]

            slug = slugify(title)[:100]

            # Create or get news instance
            news, created = News.objects.get_or_create(
                slug=slug, defaults={"title": title, "content": news_content}
            )

            # Associate document file or URL
            news.url = main_link

            # Associate thumbnail image
            if image_id and image_id in attachments_map:
                attachment = attachments_map[image_id]
                image_source_path = resolve_image_file(attachment)
                if image_source_path and os.path.exists(image_source_path):
                    image_filename = os.path.basename(image_source_path)
                    with open(image_source_path, "rb") as img_file:
                        news.thumbnail_image.save(
                            image_filename, File(img_file), save=False
                        )
                        news.thumbnail_alt_description = f"Thumbnail for {title}"

            news.save()
            imported_count += 1

    return {"status": "success", "imported_news": imported_count}
