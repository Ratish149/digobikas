import json
import os
import re
import urllib.parse

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils.text import slugify

from publication.models import Publication


def create_publication(
    *,
    title: str,
    thumbnail_image=None,
    thumbnail_alt_description: str = None,
    file=None,
    content: str = None,
    meta_title: str = None,
    meta_description: str = None,
) -> Publication:
    with transaction.atomic():
        publication = Publication(
            title=title,
            thumbnail_image=thumbnail_image,
            thumbnail_alt_description=thumbnail_alt_description,
            file=file,
            content=content,
            meta_title=meta_title,
            meta_description=meta_description,
        )
        publication.full_clean()
        publication.save()
        return publication


def update_publication(*, publication: Publication, **data) -> Publication:
    with transaction.atomic():
        for field, value in data.items():
            setattr(publication, field, value)
        publication.full_clean()
        publication.save()
        return publication


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


def parse_publications_content(content):
    """
    Parse visual composer shortcodes from the page content to extract publication columns.
    """
    columns = re.findall(r"\[vc_column.*?\](.*?)\[/vc_column\]", content, re.DOTALL)
    publications = []
    for col in columns:
        # If the column is empty or lacks single image/links, skip
        if not re.search(r"vc_single_image", col):
            continue

        image_match = re.search(r'image=["\'](\d+)["\']', col)
        image_id = int(image_match.group(1)) if image_match else None

        # Extract file link from vc_single_image or anchor tags
        link_match = re.search(r'link=["\']([^"\']+)["\']', col)
        file_link = link_match.group(1) if link_match else None

        if not file_link:
            a_match = re.search(r'<a\s+[^>]*href=["\']([^"\']+)["\']', col)
            file_link = a_match.group(1) if a_match else None

        # Extract title: concatenate all anchor tags text in the column
        a_tags = re.findall(r"<a[^>]*>(.*?)</a>", col, re.DOTALL)
        if a_tags:
            title = " ".join(re.sub(r"<[^>]+>", "", tag).strip() for tag in a_tags if tag.strip())
        else:
            # Fallback to header text
            header_match = re.search(r"<h[4-6][^>]*>(.*?)</h[4-6]>", col, re.DOTALL)
            title = re.sub(r"<[^>]+>", "", header_match.group(1)).strip() if header_match else ""

        # Clean title spaces and non-breaking spaces
        title = re.sub(r"\s+", " ", title.replace("&nbsp;", " ").replace("&#160;", " ")).strip()

        # If title is empty but we have a file_link, build it from filename
        if not title and file_link:
            parsed_url = urllib.parse.urlparse(file_link)
            title = os.path.basename(parsed_url.path).replace("-", " ").replace("_", " ").replace(".pdf", "").title()

        if file_link:
            publications.append({
                "title": title or "Research Publication",
                "image_id": image_id,
                "file_link": file_link
            })
    return publications


def import_publications() -> dict:
    """
    Imports Publications from pages.json (post_id: 395 or slug publications)
    and links the PDF files and thumbnail files.
    """
    pages_path = os.path.join(settings.BASE_DIR, "pages.json")
    attachments_path = os.path.join(settings.BASE_DIR, "attachments.json")

    if not os.path.exists(pages_path):
        raise FileNotFoundError(f"pages.json not found at {pages_path}")

    # Load pages
    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    # Find the Publications page
    target_page = None
    for page in pages:
        if page.get("post_id") == 395 or page.get("slug") == "publications":
            target_page = page
            break

    if not target_page:
        raise ValueError("Publications page not found in pages.json")

    content = target_page.get("content") or ""
    if not content:
        raise ValueError("Publications page content is empty")

    # Load attachments to resolve image IDs
    attachments_map = {}
    if os.path.exists(attachments_path):
        with open(attachments_path, "r", encoding="utf-8") as f:
            attachments = json.load(f)
            for att in attachments:
                post_id = att.get("post_id")
                if post_id:
                    attachments_map[post_id] = att

    parsed_pubs = parse_publications_content(content)
    imported_count = 0

    with transaction.atomic():
        for pub_data in parsed_pubs:
            title = pub_data["title"]
            file_link = pub_data["file_link"]
            image_id = pub_data["image_id"]

            slug = slugify(title)[:100]

            # Create or get publication instance
            publication, created = Publication.objects.get_or_create(
                slug=slug, defaults={"title": title}
            )

            # Associate document file
            parsed_url = urllib.parse.urlparse(file_link)
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
                    publication.file.save(
                        pdf_filename, File(pdf_file), save=False
                    )

            # Associate thumbnail image
            if image_id and image_id in attachments_map:
                attachment = attachments_map[image_id]
                image_source_path = resolve_image_file(attachment)
                if image_source_path and os.path.exists(image_source_path):
                    image_filename = os.path.basename(image_source_path)
                    with open(image_source_path, "rb") as img_file:
                        publication.thumbnail_image.save(
                            image_filename, File(img_file), save=False
                        )
                        publication.thumbnail_alt_description = f"Thumbnail for {title}"

            publication.save()
            imported_count += 1

    return {"status": "success", "imported_publications": imported_count}
