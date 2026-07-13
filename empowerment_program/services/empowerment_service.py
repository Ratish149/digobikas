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
from django.utils.text import slugify

from empowerment_program.models import (
    CohortVolunteer,
    EmpowermentProgram,
    EmpowermentProgramCohort,
)


def create_empowerment_program(
    *, title: str, content: str = None
) -> EmpowermentProgram:
    with transaction.atomic():
        program = EmpowermentProgram(title=title, content=content)
        program.full_clean()
        program.save()
        return program


def update_empowerment_program(
    *, program: EmpowermentProgram, **data
) -> EmpowermentProgram:
    with transaction.atomic():
        for field, value in data.items():
            setattr(program, field, value)
        program.full_clean()
        program.save()
        return program


def create_cohort(
    *,
    program: EmpowermentProgram,
    name: str,
    image=None,
    image_alt_description: str = None,
    volunteers_data: list = None,
) -> EmpowermentProgramCohort:
    with transaction.atomic():
        cohort = EmpowermentProgramCohort(
            program=program,
            name=name,
            image=image,
            image_alt_description=image_alt_description,
        )
        cohort.full_clean()
        cohort.save()

        if volunteers_data:
            for vol_data in volunteers_data:
                volunteer = CohortVolunteer(
                    cohort=cohort,
                    name=vol_data.get("name"),
                    image=vol_data.get("image"),
                    image_alt_description=vol_data.get("image_alt_description"),
                )
                volunteer.full_clean()
                volunteer.save()

        return cohort


def update_cohort(
    *, cohort: EmpowermentProgramCohort, **data
) -> EmpowermentProgramCohort:
    volunteers_data = data.pop("volunteers", None)
    with transaction.atomic():
        for field, value in data.items():
            setattr(cohort, field, value)
        cohort.full_clean()
        cohort.save()

        if volunteers_data is not None:
            keep_volunteers = []
            for vol_item in volunteers_data:
                vol_id = vol_item.get("id")
                if vol_id:
                    try:
                        volunteer = CohortVolunteer.objects.get(
                            id=vol_id, cohort=cohort
                        )
                        for k, v in vol_item.items():
                            if k != "id":
                                setattr(volunteer, k, v)
                        volunteer.full_clean()
                        volunteer.save()
                        keep_volunteers.append(volunteer.id)
                    except CohortVolunteer.DoesNotExist:
                        pass
                else:
                    volunteer = CohortVolunteer(
                        cohort=cohort,
                        name=vol_item.get("name"),
                        image=vol_item.get("image"),
                        image_alt_description=vol_item.get("image_alt_description"),
                    )
                    volunteer.full_clean()
                    volunteer.save()
                    keep_volunteers.append(volunteer.id)

            cohort.volunteers.exclude(id__in=keep_volunteers).delete()

        return cohort


def create_cohort_volunteer(
    *,
    cohort: EmpowermentProgramCohort,
    name: str,
    image=None,
    image_alt_description: str = None,
) -> CohortVolunteer:
    with transaction.atomic():
        volunteer = CohortVolunteer(
            cohort=cohort,
            name=name,
            image=image,
            image_alt_description=image_alt_description,
        )
        volunteer.full_clean()
        volunteer.save()
        return volunteer


def update_cohort_volunteer(
    *, cohort_volunteer: CohortVolunteer, **data
) -> CohortVolunteer:
    with transaction.atomic():
        for field, value in data.items():
            setattr(cohort_volunteer, field, value)
        cohort_volunteer.full_clean()
        cohort_volunteer.save()
        return cohort_volunteer


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


def save_image_to_field(model_instance, field_name, image_id, attachments_map):
    if not image_id or image_id not in attachments_map:
        return False
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
            prefix = dir_part.replace("/", "_").replace("\\", "_") if dir_part else ""

            media_dir = os.path.join(settings.BASE_DIR, "media")
            url = att.get("attachment_url") or att.get("guid", "")
            if url:
                target_filename = f"{prefix}_{basename}" if prefix else basename
                target_path = os.path.join(media_dir, target_filename)
                if download_file_with_fallback(url, target_path):
                    image_path = target_path

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            field = getattr(model_instance, field_name)
            field.save(os.path.basename(image_path), File(img_file), save=False)
        # Set alt text if present
        alt_text = att.get("postmeta", {}).get("_wp_attachment_image_alt", "")
        if isinstance(alt_text, list):
            alt_text = alt_text[0] if alt_text else ""
        if alt_text:
            model_instance.image_alt_description = alt_text
        return True
    return False


def import_empowerment_programs() -> dict:
    pages_path = os.path.join(settings.BASE_DIR, "pages.json")
    attachments_path = os.path.join(settings.BASE_DIR, "attachments.json")

    if not os.path.exists(pages_path):
        raise FileNotFoundError(f"pages.json not found at {pages_path}")

    # Load pages
    with open(pages_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    # Load attachments to resolve image IDs
    attachments_map = {}
    if os.path.exists(attachments_path):
        with open(attachments_path, "r", encoding="utf-8") as f:
            attachments = json.load(f)
            for att in attachments:
                post_id = att.get("post_id")
                if post_id:
                    attachments_map[post_id] = att

    # Group pages by slug
    pages_by_slug = {}
    for p in pages:
        slug_val = p.get("slug")
        if slug_val:
            pages_by_slug[slug_val] = p

    programs_created = 0
    cohorts_created = 0
    volunteers_created = 0

    with transaction.atomic():
        # ----------------------------------------------------
        # Program 1: Green City Volunteers
        # ----------------------------------------------------
        gcv_page = pages_by_slug.get("green-city-volunteer-2023")
        if gcv_page:
            title = gcv_page.get("title") or "Green City Volunteers"
            content = gcv_page.get("content") or ""
            cleaned_content = clean_wp_content(content)

            # Create or get Empowerment Program
            program, created = EmpowermentProgram.objects.get_or_create(
                slug="green-city-volunteer-2023",
                defaults={"title": title, "content": cleaned_content},
            )
            if created:
                programs_created += 1
            else:
                program.title = title
                program.content = cleaned_content
                program.save()

            # Parse cohorts from Green City Volunteers content columns
            columns = re.findall(
                r"\[vc_column[^\]]*\](.*?)\[/vc_column\]", content, re.DOTALL
            )
            for col in columns:
                if "gcv-biratnagar" not in col:
                    continue
                # Extract image ID for the cohort
                img_match = re.search(r'image=["\'](\d+)["\']', col)
                cohort_image_id = int(img_match.group(1)) if img_match else None

                # Extract link to find the slug
                link_match = re.search(r'link=["\']([^"\']+)["\']', col)
                if not link_match:
                    link_match = re.search(r'href=["\']([^"\']+)["\']', col)

                if link_match:
                    cohort_url = link_match.group(1)
                    parsed_url = urllib.parse.urlparse(cohort_url)
                    cohort_slug = parsed_url.path.strip("/").split("/")[-1]

                    # Retrieve cohort page to get exact title and contents
                    cohort_page = pages_by_slug.get(cohort_slug)
                    if cohort_page:
                        cohort_name = cohort_page.get("title")
                        cohort_content = cohort_page.get("content") or ""

                        # Create or get Cohort
                        cohort, c_created = (
                            EmpowermentProgramCohort.objects.get_or_create(
                                slug=cohort_slug,
                                defaults={"program": program, "name": cohort_name},
                            )
                        )
                        if c_created:
                            cohorts_created += 1
                        else:
                            cohort.program = program
                            cohort.name = cohort_name
                            cohort.save()

                        # Save Cohort image
                        if cohort_image_id:
                            save_image_to_field(
                                cohort, "image", cohort_image_id, attachments_map
                            )
                            cohort.save()

                        # Parse and create volunteers if they exist
                        vol_columns = re.findall(
                            r"\[vc_column[^\]]*\](.*?)\[/vc_column\]",
                            cohort_content,
                            re.DOTALL,
                        )
                        for vol_col in vol_columns:
                            vol_img_match = re.search(r'image=["\'](\d+)["\']', vol_col)
                            vol_name_match = re.search(
                                r"<h[1-6][^>]*>(.*?)</h[1-6]>", vol_col, re.DOTALL
                            )

                            if vol_name_match:
                                vol_name = re.sub(
                                    r"<[^>]+>", "", vol_name_match.group(1)
                                ).strip()
                                vol_name = html.unescape(vol_name)
                                if not vol_name:
                                    continue

                                # Create or get Volunteer
                                volunteer, v_created = (
                                    CohortVolunteer.objects.get_or_create(
                                        cohort=cohort,
                                        name=vol_name,
                                    )
                                )
                                if v_created:
                                    volunteers_created += 1

                                # Save Volunteer image
                                if vol_img_match:
                                    vol_image_id = int(vol_img_match.group(1))
                                    save_image_to_field(
                                        volunteer,
                                        "image",
                                        vol_image_id,
                                        attachments_map,
                                    )
                                    volunteer.save()

        # ----------------------------------------------------
        # Program 2: Climate Justice Summer School
        # ----------------------------------------------------
        cjss_page = pages_by_slug.get("climate-justice-summer-school-2023")
        if cjss_page:
            title = cjss_page.get("title") or "Climate Justice Summer School"
            content = cjss_page.get("content") or ""
            cleaned_content = clean_wp_content(content)

            # Create or get Empowerment Program
            program, created = EmpowermentProgram.objects.get_or_create(
                slug="climate-justice-summer-school-2023",
                defaults={"title": title, "content": cleaned_content},
            )
            if created:
                programs_created += 1
            else:
                program.title = title
                program.content = cleaned_content
                program.save()

            # Parse cohorts from Climate Justice Summer School content using text separators
            separators = list(
                re.finditer(r'\[vc_text_separator title="([^"]+)"', content)
            )
            for idx, match in enumerate(separators):
                cohort_name = match.group(1).strip()
                start = match.end()
                end = (
                    separators[idx + 1].start()
                    if idx + 1 < len(separators)
                    else len(content)
                )
                sec_content = content[start:end]

                # Find the single image tag in this section
                img_match = re.search(r'image=["\'](\d+)["\']', sec_content)
                cohort_image_id = int(img_match.group(1)) if img_match else None

                cohort_slug = slugify(cohort_name)[:100]

                # Create or get Cohort
                cohort, c_created = EmpowermentProgramCohort.objects.get_or_create(
                    slug=cohort_slug, defaults={"program": program, "name": cohort_name}
                )
                if c_created:
                    cohorts_created += 1
                else:
                    cohort.program = program
                    cohort.name = cohort_name
                    cohort.save()

                # Save Cohort image
                if cohort_image_id:
                    save_image_to_field(
                        cohort, "image", cohort_image_id, attachments_map
                    )
                    cohort.save()

    return {
        "status": "success",
        "programs_created": programs_created,
        "cohorts_created": cohorts_created,
        "volunteers_created": volunteers_created,
    }
