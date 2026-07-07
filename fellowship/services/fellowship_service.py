import html
import json
import os
import re
import time
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.files import File
from django.db import transaction

from fellowship.models import Fellowship, FellowshipMember


def create_fellowship(*, title: str, members_data: list = None) -> Fellowship:
    """
    Creates a new Fellowship along with any nested FellowshipMembers atomically.
    """
    with transaction.atomic():
        fellowship = Fellowship(title=title)
        fellowship.full_clean()
        fellowship.save()

        if members_data:
            for member_data in members_data:
                member = FellowshipMember(
                    fellowship=fellowship,
                    name=member_data.get("name"),
                    description=member_data.get("description"),
                    image=member_data.get("image"),
                )
                member.full_clean()
                member.save()

        return fellowship


def update_fellowship(*, fellowship: Fellowship, **data) -> Fellowship:
    """
    Updates a Fellowship and its nested FellowshipMembers atomically.
    """
    members_data = data.pop("members", None)
    with transaction.atomic():
        for field, value in data.items():
            setattr(fellowship, field, value)
        fellowship.full_clean()
        fellowship.save()

        if members_data is not None:
            keep_members = []
            for member_item in members_data:
                member_id = member_item.get("id")
                if member_id:
                    try:
                        member = FellowshipMember.objects.get(
                            id=member_id, fellowship=fellowship
                        )
                        for k, v in member_item.items():
                            if k != "id":
                                setattr(member, k, v)
                        member.full_clean()
                        member.save()
                        keep_members.append(member.id)
                    except FellowshipMember.DoesNotExist:
                        pass
                else:
                    member = FellowshipMember(
                        fellowship=fellowship,
                        name=member_item.get("name"),
                        description=member_item.get("description"),
                        image=member_item.get("image"),
                    )
                    member.full_clean()
                    member.save()
                    keep_members.append(member.id)

            fellowship.members.exclude(id__in=keep_members).delete()

        return fellowship


def create_fellowship_member(
    *, fellowship: Fellowship, name: str, description: str, image
) -> FellowshipMember:
    """
    Creates a standalone FellowshipMember.
    """
    with transaction.atomic():
        member = FellowshipMember(
            fellowship=fellowship,
            name=name,
            description=description,
            image=image,
        )
        member.full_clean()
        member.save()
        return member


def update_fellowship_member(
    *, fellowship_member: FellowshipMember, **data
) -> FellowshipMember:
    """
    Updates a standalone FellowshipMember.
    """
    with transaction.atomic():
        for field, value in data.items():
            setattr(fellowship_member, field, value)
        fellowship_member.full_clean()
        fellowship_member.save()
        return fellowship_member


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
    if os.path.exists(path_plain) and os.path.getsize(path_plain) > 0:
        return path_plain

    # 2. Check prefixed version (e.g. 2020_11_Rethinking.jpg)
    if prefix:
        path_prefixed = os.path.join(media_dir, f"{prefix}_{basename}")
        if os.path.exists(path_prefixed) and os.path.getsize(path_prefixed) > 0:
            return path_prefixed

    return None


def download_file_with_fallback(url, local_path, timeout=10, retries=3):
    """
    Downloads a file from url and saves it to local_path.
    Tries primary URL first, falling back to Wayback Machine.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # Step 1: Try original URL
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            with open(local_path, "wb") as out_file:
                out_file.write(response.read())
            return True
    except Exception:
        pass

    # Step 2: Query Wayback Machine Availability API
    try:
        api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(url)}"
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            snapshots = data.get("archived_snapshots", {})
            closest = snapshots.get("closest", {})
            if closest.get("available") and closest.get("url"):
                wb_url = closest["url"]
                # Convert page URL to raw media URL in Wayback Machine (adding 'im_')
                wb_url = re.sub(r"/web/(\d{14})/", r"/web/\1im_/", wb_url)

                # Download from Wayback Machine
                for attempt in range(1, retries + 1):
                    try:
                        req_wb = urllib.request.Request(wb_url, headers=headers)
                        with urllib.request.urlopen(
                            req_wb, timeout=timeout
                        ) as response_wb:
                            with open(local_path, "wb") as out_file:
                                out_file.write(response_wb.read())
                            return True
                    except Exception:
                        time.sleep(1)
    except Exception:
        pass

    return False


def import_fellowships() -> dict:
    """
    Imports Fellowships and FellowshipMembers from pages.json (post_id: 535)
    and resolves/downloads their photos and descriptions.
    """
    pages_path = os.path.join(settings.BASE_DIR, "pages.json")
    attachments_path = os.path.join(settings.BASE_DIR, "attachments.json")

    if not os.path.exists(pages_path):
        raise FileNotFoundError(f"pages.json not found at {pages_path}")

    # Load pages
    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    # Find the Fellowship page
    target_page = None
    for page in pages:
        if page.get("post_id") == 535:
            target_page = page
            break

    if not target_page:
        raise ValueError("Research Fellowship page not found in pages.json")

    content = target_page.get("content") or ""
    if not content:
        raise ValueError("Research Fellowship page content is empty")

    # Load attachments to resolve image IDs
    attachments_map = {}
    if os.path.exists(attachments_path):
        with open(attachments_path, "r", encoding="utf-8") as f:
            attachments = json.load(f)
            for att in attachments:
                p_id = att.get("post_id")
                if p_id:
                    attachments_map[p_id] = att

    # Load all pages to resolve member descriptions
    pages_by_id = {}
    pages_by_slug = {}
    pages_by_title = {}
    for page in pages:
        p_id = page.get("post_id")
        if p_id:
            pages_by_id[p_id] = page
        slug_val = page.get("slug")
        if slug_val:
            pages_by_slug[slug_val] = page
        title_val = page.get("title")
        if title_val:
            pages_by_title[title_val.strip().lower()] = page

    def clean_wp_content(raw_content):
        if not raw_content:
            return ""
        # Remove vc shortcodes
        raw_content = re.sub(r"\[/?vc_[^\]]*\]", "", raw_content)
        # Remove HTML tags
        raw_content = re.sub(r"<[^>]+>", "", raw_content)
        # Unescape html entities
        raw_content = html.unescape(raw_content)
        # Normalize whitespace
        raw_content = re.sub(r"\s+", " ", raw_content)
        return raw_content.strip()

    # Helper: resolve member description
    def get_member_description(member_name, link):
        parsed = urllib.parse.urlparse(link)
        query = urllib.parse.parse_qs(parsed.query)
        page_id_list = query.get("page_id")

        member_page = None
        if page_id_list:
            try:
                page_id = int(page_id_list[0])
                member_page = pages_by_id.get(page_id)
            except ValueError:
                pass

        if not member_page and parsed.path:
            slug_part = parsed.path.strip("/").split("/")[-1]
            member_page = pages_by_slug.get(slug_part)

        if not member_page:
            member_page = pages_by_title.get(member_name.strip().lower())

        if member_page:
            raw_content = member_page.get("content", "")
            return clean_wp_content(raw_content)
        return ""

    # Group by Fellowship title using separators
    separators = list(re.finditer(r'\[vc_text_separator title="([^"]+)"', content))
    sections = []
    for idx, match in enumerate(separators):
        f_title = match.group(1).strip()
        start = match.end()
        end = separators[idx + 1].start() if idx + 1 < len(separators) else len(content)
        section_content = content[start:end]
        sections.append((f_title, section_content))

    imported_fellowships = []
    fellowships_created = 0
    members_created = 0

    with transaction.atomic():
        for f_title, sec_content in sections:
            # Create or get fellowship
            fellowship, f_created = Fellowship.objects.get_or_create(title=f_title)
            if f_created:
                fellowships_created += 1

            # Find all members in this section
            matches = re.findall(
                r'image="(\d+)"[^\]]*?.*?<a\s+href="([^"]+)"[^>]*>(.*?)</a>',
                sec_content,
                re.DOTALL,
            )

            for image_id_str, link, name in matches:
                name = html.unescape(name).strip()
                image_id = int(image_id_str)
                description = get_member_description(name, link)

                # Get or create member within the fellowship
                member, m_created = FellowshipMember.objects.get_or_create(
                    fellowship=fellowship,
                    name=name,
                    defaults={"description": description},
                )
                if m_created:
                    members_created += 1
                else:
                    if description and member.description != description:
                        member.description = description
                        member.save()

                # Resolve and save image
                if image_id in attachments_map:
                    att = attachments_map[image_id]
                    image_path = resolve_image_file(att)

                    # If not found locally, download it
                    if not image_path:
                        rel_path = att.get("postmeta", {}).get("_wp_attached_file")
                        if not rel_path:
                            url = att.get("attachment_url") or att.get("guid", "")
                            parsed_url = urllib.parse.urlparse(url)
                            rel_path = os.path.basename(parsed_url.path)

                        if isinstance(rel_path, list):
                            rel_path = rel_path[0]

                        if rel_path:
                            basename = os.path.basename(rel_path)
                            dir_part = os.path.dirname(rel_path)
                            prefix = (
                                dir_part.replace("/", "_").replace("\\", "_")
                                if dir_part
                                else ""
                            )

                            media_dir = os.path.join(settings.BASE_DIR, "media")
                            url = att.get("attachment_url") or att.get("guid", "")
                            if url:
                                target_filename = (
                                    f"{prefix}_{basename}" if prefix else basename
                                )
                                target_path = os.path.join(media_dir, target_filename)
                                if download_file_with_fallback(url, target_path):
                                    image_path = target_path

                    if image_path:
                        with open(image_path, "rb") as img_file:
                            member.image.save(
                                os.path.basename(image_path),
                                File(img_file),
                                save=True,
                            )

            imported_fellowships.append(fellowship.title)

    return {
        "status": "success",
        "fellowships_created": fellowships_created,
        "members_created": members_created,
        "imported_fellowships": imported_fellowships,
    }
