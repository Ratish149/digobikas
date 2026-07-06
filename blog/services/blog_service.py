import json
import os
import re
import urllib.parse

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils.text import slugify

from blog.models import Blog


def create_blog(
    *,
    title: str,
    thumbnail_image=None,
    thumbnail_alt_description: str = None,
    file=None,
    content: str = None,
    url: str = None,
    meta_title: str = None,
    meta_description: str = None,
) -> Blog:
    with transaction.atomic():
        blog = Blog(
            title=title,
            thumbnail_image=thumbnail_image,
            thumbnail_alt_description=thumbnail_alt_description,
            file=file,
            content=content,
            url=url,
            meta_title=meta_title,
            meta_description=meta_description,
        )
        blog.full_clean()
        blog.save()
        return blog


def update_blog(*, blog: Blog, **data) -> Blog:
    with transaction.atomic():
        for field, value in data.items():
            setattr(blog, field, value)
        blog.full_clean()
        blog.save()
        return blog


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


def parse_blogs_content(content):
    """
    Parse visual composer shortcodes from the page content to extract blogs.
    """
    columns = re.findall(r"\[vc_column.*?\](.*?)\[/vc_column\]", content, re.DOTALL)
    blogs = []
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

        # Extract Title: text inside h3/h4/h5 tags
        title_match = (
            re.search(r"<h3[^>]*>(.*?)</h3>", col, re.DOTALL)
            or re.search(r"<h4[^>]*>(.*?)</h4>", col, re.DOTALL)
            or re.search(r"<h5[^>]*>(.*?)</h5>", col, re.DOTALL)
        )
        if title_match:
            title = re.sub(r"<[^>]+>", "", title_match.group(1))
        else:
            title = ""

        title = title.replace("&nbsp;", " ").replace("&#160;", " ").strip()

        # Extract Content/Author (e.g. from h6)
        author_match = re.search(r"<h6>(.*?)</h6>", col, re.DOTALL)
        blog_content = ""
        if author_match:
            blog_content = re.sub(r"<[^>]+>", "", author_match.group(1))
            blog_content = (
                blog_content.replace("&nbsp;", " ").replace("&#160;", " ").strip()
            )

        if title and main_link:
            blogs.append({
                "title": title,
                "image_id": image_id,
                "main_link": main_link,
                "content": blog_content,
            })
    return blogs


def import_blogs() -> dict:
    """
    Imports Blogs from pages.json (post_id: 1410 or slug blog)
    and links the document/URL and thumbnail files.
    """
    pages_path = os.path.join(settings.BASE_DIR, "pages.json")
    attachments_path = os.path.join(settings.BASE_DIR, "attachments.json")

    if not os.path.exists(pages_path):
        raise FileNotFoundError(f"pages.json not found at {pages_path}")

    # Load pages
    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    # Find the News Articles / Blogs page
    target_page = None
    for page in pages:
        if page.get("post_id") == 1410 or page.get("slug") == "blog":
            target_page = page
            break

    if not target_page:
        raise ValueError("News Articles / Blogs page not found in pages.json")

    content = target_page.get("content") or ""
    if not content:
        raise ValueError("News Articles / Blogs page content is empty")

    # Load attachments to resolve image IDs
    attachments_map = {}
    if os.path.exists(attachments_path):
        with open(attachments_path, "r", encoding="utf-8") as f:
            attachments = json.load(f)
            for att in attachments:
                post_id = att.get("post_id")
                if post_id:
                    attachments_map[post_id] = att

    parsed_blogs = parse_blogs_content(content)
    imported_count = 0

    with transaction.atomic():
        for blog_data in parsed_blogs:
            title = blog_data["title"]
            main_link = blog_data["main_link"]
            image_id = blog_data["image_id"]
            blog_content = blog_data["content"]

            slug = slugify(title)[:100]

            # Create or get blog instance
            blog, created = Blog.objects.get_or_create(
                slug=slug, defaults={"title": title, "content": blog_content}
            )

            # Associate document file or URL
            parsed_url = urllib.parse.urlparse(main_link)
            path_lower = parsed_url.path.lower()
            if path_lower.endswith(".pdf") or "/uploads/" in path_lower:
                pdf_filename = os.path.basename(parsed_url.path)
                # Check in flat media directory
                source_pdf_path = os.path.join(settings.BASE_DIR, "media", pdf_filename)
                # If not found, check prefixed version in media
                if not os.path.exists(source_pdf_path):
                    media_dir = os.path.join(settings.BASE_DIR, "media")
                    for f in os.listdir(media_dir):
                        if f.endswith(pdf_filename):
                            source_pdf_path = os.path.join(media_dir, f)
                            break

                if os.path.exists(source_pdf_path):
                    with open(source_pdf_path, "rb") as pdf_file:
                        blog.file.save(pdf_filename, File(pdf_file), save=False)
            else:
                blog.url = main_link

            # Associate thumbnail image
            if image_id and image_id in attachments_map:
                attachment = attachments_map[image_id]
                image_source_path = resolve_image_file(attachment)
                if image_source_path and os.path.exists(image_source_path):
                    image_filename = os.path.basename(image_source_path)
                    with open(image_source_path, "rb") as img_file:
                        blog.thumbnail_image.save(
                            image_filename, File(img_file), save=False
                        )
                        blog.thumbnail_alt_description = f"Thumbnail for {title}"

            blog.save()
            imported_count += 1

    return {"status": "success", "imported_blogs": imported_count}
