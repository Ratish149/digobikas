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

from team.models import TeamMember


def create_team_member(
    *,
    name: str,
    member_type: str = "board_member",
    designation: str = None,
    description: str = "",
    image=None,
) -> TeamMember:
    with transaction.atomic():
        member = TeamMember(
            name=name,
            member_type=member_type,
            designation=designation,
            description=description,
            image=image,
        )
        member.full_clean()
        member.save()
        return member


def update_team_member(*, team_member: TeamMember, **data) -> TeamMember:
    with transaction.atomic():
        for field, value in data.items():
            setattr(team_member, field, value)
        team_member.full_clean()
        team_member.save()
        return team_member


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

    # 1. Check plain basename
    path_plain = os.path.join(media_dir, basename)
    if os.path.exists(path_plain) and os.path.getsize(path_plain) > 0:
        return path_plain

    # 2. Check prefixed version
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

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            with open(local_path, "wb") as out_file:
                out_file.write(response.read())
            return True
    except Exception:
        pass

    try:
        api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(url)}"
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            snapshots = data.get("archived_snapshots", {})
            closest = snapshots.get("closest", {})
            if closest.get("available") and closest.get("url"):
                wb_url = closest["url"]
                wb_url = re.sub(r"/web/(\d{14})/", r"/web/\1im_/", wb_url)

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


def parse_team_columns(content):
    """
    Parse visual composer shortcodes to extract team members.
    """
    columns = re.findall(r"\[vc_column[^\]]*\](.*?)\[/vc_column\]", content, re.DOTALL)
    results = []
    for col in columns:
        col = col.strip()
        if not col:
            continue

        # 1. Extract image ID if present
        image_match = re.search(r'image=["\'](\d+)["\']', col)
        image_id = int(image_match.group(1)) if image_match else None

        # 2. Extract name and link
        name = ""
        link = ""
        a_match = re.search(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', col, re.DOTALL)
        if a_match:
            link = a_match.group(1).strip()
            name = a_match.group(2)
        else:
            h_match = re.search(r"<h[45][^>]*>(.*?)</h[45]>", col, re.DOTALL)
            if h_match:
                name = h_match.group(1)

        if name:
            name = re.sub(r"<[^>]+>", "", name)
            name = html.unescape(name).replace("\xa0", " ").strip()

        if not name:
            continue

        # 3. Extract designation
        designation = ""
        p_match = re.search(r"<p[^>]*>(.*?)</p>", col, re.DOTALL)
        if p_match:
            designation = re.sub(r"<[^>]+>", "", p_match.group(1))
            designation = html.unescape(designation).strip()

        results.append({
            "name": name,
            "link": link,
            "image_id": image_id,
            "designation": designation,
        })
    return results


def import_team() -> dict:
    """
    Imports Board Members and Staff from pages.json (post_id: 539, 542)
    and resolves/downloads their photos and descriptions.
    """
    pages_path = os.path.join(settings.BASE_DIR, "pages.json")
    attachments_path = os.path.join(settings.BASE_DIR, "attachments.json")

    if not os.path.exists(pages_path):
        raise FileNotFoundError(f"pages.json not found at {pages_path}")

    # Load pages
    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    # Find the Board Members (539) and Staff (542) pages
    board_page = None
    staff_page = None
    for page in pages:
        p_id = page.get("post_id")
        if p_id == 539:
            board_page = page
        elif p_id == 542:
            staff_page = page

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

    def get_member_description(member_name, link):
        if not link:
            return ""
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

    imported_members = []
    members_created = 0

    with transaction.atomic():
        # 1. Process Board Members
        if board_page:
            content = board_page.get("content") or ""
            board_members_data = parse_team_columns(content)
            for item in board_members_data:
                name = item["name"]
                link = item["link"]
                image_id = item["image_id"]
                designation = item["designation"] or "Board Member"
                description = get_member_description(name, link)

                member, created = TeamMember.objects.get_or_create(
                    name=name,
                    member_type="board_member",
                    defaults={
                        "designation": designation,
                        "description": description,
                    },
                )
                if created:
                    members_created += 1
                else:
                    member.designation = designation
                    if description:
                        member.description = description
                    member.save()

                # Process image
                if image_id and image_id in attachments_map:
                    att = attachments_map[image_id]
                    image_path = resolve_image_file(att)

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

                imported_members.append(member.name)

        # 2. Process Staff
        if staff_page:
            content = staff_page.get("content") or ""
            staff_data = parse_team_columns(content)
            for item in staff_data:
                name = item["name"]
                link = item["link"]
                image_id = item["image_id"]
                designation = item["designation"] or "Staff"
                description = get_member_description(name, link)

                member, created = TeamMember.objects.get_or_create(
                    name=name,
                    member_type="staff",
                    defaults={
                        "designation": designation,
                        "description": description,
                    },
                )
                if created:
                    members_created += 1
                else:
                    member.designation = designation
                    if description:
                        member.description = description
                    member.save()

                # Process image
                if image_id and image_id in attachments_map:
                    att = attachments_map[image_id]
                    image_path = resolve_image_file(att)

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

                imported_members.append(member.name)

    return {
        "status": "success",
        "members_created": members_created,
        "imported_members": imported_members,
    }
