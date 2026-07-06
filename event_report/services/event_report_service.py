import json
import os
import re
import urllib.parse

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils.text import slugify

from event_report.models import EventReport


def create_event_report(
    *,
    title: str,
    thumbnail_image=None,
    thumbnail_alt_description: str = None,
    file=None,
    content=None,
    meta_title: str = None,
    meta_description: str = None,
) -> EventReport:
    with transaction.atomic():
        event_report = EventReport(
            title=title,
            thumbnail_image=thumbnail_image,
            thumbnail_alt_description=thumbnail_alt_description,
            file=file,
            content=content,
            meta_title=meta_title,
            meta_description=meta_description,
        )
        event_report.full_clean()
        event_report.save()
        return event_report


def update_event_report(*, event_report: EventReport, **data) -> EventReport:
    with transaction.atomic():
        for field, value in data.items():
            setattr(event_report, field, value)
        event_report.full_clean()
        event_report.save()
        return event_report


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


def parse_event_reports_content(content):
    """
    Parse visual composer shortcodes from the page content to extract report info.
    """
    columns = re.findall(r"\[vc_column.*?\](.*?)\[/vc_column\]", content, re.DOTALL)
    reports = []
    for col in columns:
        # Extract image ID
        image_match = re.search(r'vc_single_image\s+[^\]]*image=["\'](\d+)["\']', col)
        image_id = int(image_match.group(1)) if image_match else None

        # Extract PDF document link
        link_match = re.search(r'vc_single_image\s+[^\]]*link=["\']([^"\']+)["\']', col)
        pdf_link = link_match.group(1) if link_match else None
        if not pdf_link:
            a_match = re.search(r'<a\s+[^>]*href=["\']([^"\']+)["\']', col)
            pdf_link = a_match.group(1) if a_match else None

        # Extract Title
        title_match = re.search(r"<a\s+[^>]*>(.*?)</a>", col, re.DOTALL)
        if not title_match:
            title_match = re.search(r"<h5[^>]*>(.*?)</h5>", col, re.DOTALL)

        title = ""
        if title_match:
            title = re.sub(r"<[^>]+>", "", title_match.group(1))
            title = title.replace("&nbsp;", " ").replace("&#160;", " ").strip()

        if title and pdf_link:
            reports.append({"title": title, "image_id": image_id, "pdf_link": pdf_link})

    return reports


def import_event_reports() -> dict:
    """
    Imports Event Reports from pages.json (post_id: 1408 or slug event-reports)
    and links the document and thumbnail files.
    """
    pages_path = os.path.join(settings.BASE_DIR, "pages.json")
    attachments_path = os.path.join(settings.BASE_DIR, "attachments.json")

    if not os.path.exists(pages_path):
        raise FileNotFoundError(f"pages.json not found at {pages_path}")

    # Load pages
    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    # Find the Event Reports page
    target_page = None
    for page in pages:
        if page.get("post_id") == 1408 or page.get("slug") == "event-reports":
            target_page = page
            break

    if not target_page:
        raise ValueError("Event Reports page not found in pages.json")

    content = target_page.get("content") or ""
    if not content:
        raise ValueError("Event Reports page content is empty")

    # Load attachments to resolve image IDs
    attachments_map = {}
    if os.path.exists(attachments_path):
        with open(attachments_path, "r", encoding="utf-8") as f:
            attachments = json.load(f)
            for att in attachments:
                post_id = att.get("post_id")
                if post_id:
                    attachments_map[post_id] = att

    parsed_reports = parse_event_reports_content(content)
    imported_count = 0

    with transaction.atomic():
        for report in parsed_reports:
            title = report["title"]
            pdf_link = report["pdf_link"]
            image_id = report["image_id"]

            slug = slugify(title)[:100]

            # Create or get event report instance
            event_report, created = EventReport.objects.get_or_create(
                slug=slug, defaults={"title": title}
            )

            # Associate document file
            pdf_filename = os.path.basename(urllib.parse.urlparse(pdf_link).path)
            # Check in flat media directory
            source_pdf_path = os.path.join(settings.BASE_DIR, "media", pdf_filename)
            # If not found, check prefixed version in media
            if not os.path.exists(source_pdf_path):
                # Try locating files containing the name in media
                media_dir = os.path.join(settings.BASE_DIR, "media")
                for f in os.listdir(media_dir):
                    if f.endswith(pdf_filename):
                        source_pdf_path = os.path.join(media_dir, f)
                        break

            if os.path.exists(source_pdf_path):
                with open(source_pdf_path, "rb") as pdf_file:
                    event_report.file.save(pdf_filename, File(pdf_file), save=False)

            # Associate thumbnail image
            if image_id and image_id in attachments_map:
                attachment = attachments_map[image_id]
                image_source_path = resolve_image_file(attachment)
                if image_source_path and os.path.exists(image_source_path):
                    image_filename = os.path.basename(image_source_path)
                    with open(image_source_path, "rb") as img_file:
                        event_report.thumbnail_image.save(
                            image_filename, File(img_file), save=False
                        )
                        event_report.thumbnail_alt_description = (
                            f"Thumbnail for {title}"
                        )

            event_report.save()
            imported_count += 1

    return {"status": "success", "imported_reports": imported_count}
