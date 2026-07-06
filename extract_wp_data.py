#!/usr/bin/env python3
import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

# WXR namespaces
NAMESPACES = {
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wfw": "http://wellformedweb.org/CommentAPI/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "wp": "http://wordpress.org/export/1.2/",
}


def get_element_text(element, path, namespaces=None):
    el = element.find(path, namespaces) if namespaces else element.find(path)
    return el.text if el is not None else ""


def parse_item(item, namespaces):
    categories = []
    for cat_el in item.findall("category"):
        categories.append({
            "domain": cat_el.attrib.get("domain", ""),
            "slug": cat_el.attrib.get("nicename", ""),
            "name": cat_el.text or "",
        })

    postmeta = {}
    for meta_el in item.findall("wp:postmeta", namespaces):
        key_el = meta_el.find("wp:meta_key", namespaces)
        val_el = meta_el.find("wp:meta_value", namespaces)
        if key_el is not None and val_el is not None:
            key = key_el.text
            val = val_el.text or ""
            # Aggregate duplicate keys as a list
            if key in postmeta:
                if isinstance(postmeta[key], list):
                    postmeta[key].append(val)
                else:
                    postmeta[key] = [postmeta[key], val]
            else:
                postmeta[key] = val

    guid_el = item.find("guid")
    guid_is_permalink = True
    if guid_el is not None:
        guid_is_permalink = guid_el.attrib.get("isPermaLink", "true") == "true"

    return {
        "title": get_element_text(item, "title"),
        "link": get_element_text(item, "link"),
        "pubDate": get_element_text(item, "pubDate"),
        "creator": get_element_text(item, "dc:creator", namespaces),
        "guid": get_element_text(item, "guid"),
        "guid_is_permalink": guid_is_permalink,
        "description": get_element_text(item, "description"),
        "content": get_element_text(item, "content:encoded", namespaces),
        "excerpt": get_element_text(item, "excerpt:encoded", namespaces),
        "post_id": int(get_element_text(item, "wp:post_id", namespaces) or 0),
        "post_date": get_element_text(item, "wp:post_date", namespaces),
        "post_date_gmt": get_element_text(item, "wp:post_date_gmt", namespaces),
        "comment_status": get_element_text(item, "wp:comment_status", namespaces),
        "ping_status": get_element_text(item, "wp:ping_status", namespaces),
        "slug": get_element_text(item, "wp:post_name", namespaces),
        "status": get_element_text(item, "wp:status", namespaces),
        "post_parent": int(get_element_text(item, "wp:post_parent", namespaces) or 0),
        "menu_order": int(get_element_text(item, "wp:menu_order", namespaces) or 0),
        "post_type": get_element_text(item, "wp:post_type", namespaces),
        "post_password": get_element_text(item, "wp:post_password", namespaces),
        "is_sticky": int(get_element_text(item, "wp:is_sticky", namespaces) or 0),
        "attachment_url": get_element_text(item, "wp:attachment_url", namespaces),
        "categories": categories,
        "postmeta": postmeta,
    }


def get_wayback_url(original_url, timeout=10):
    """Queries the Wayback Machine Availability API for an archived version of a URL."""
    try:
        api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(original_url)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            snapshots = data.get("archived_snapshots", {})
            closest = snapshots.get("closest", {})
            if closest.get("available") and closest.get("url"):
                wb_url = closest["url"]
                # Convert page URL to raw media URL in Wayback Machine (adding 'im_')
                wb_url = re.sub(r"/web/(\d{14})/", r"/web/\1im_/", wb_url)
                return wb_url
    except Exception:
        pass
    return None


def download_file(url, local_path, timeout=10):
    """Downloads a file from url and saves it to local_path. Returns (success, url, local_path, error_msg)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Check if a valid non-HTML file already exists
    if os.path.exists(local_path):
        if os.path.getsize(local_path) > 0:
            try:
                with open(local_path, "rb") as f:
                    start_bytes = f.read(20)
                # If it doesn't look like an HTML/text file, consider it valid and skip re-downloading
                if not (
                    start_bytes.startswith(b"<")
                    or start_bytes.startswith(b"<!")
                    or start_bytes.startswith(b"\n<")
                ):
                    return True, url, local_path, "Already Exists"
            except Exception:
                pass
        # Delete invalid (HTML-challenge or empty) files
        try:
            os.remove(local_path)
        except Exception:
            pass

    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content_type = response.info().get_content_type()
            if content_type == "text/html":
                return (
                    False,
                    url,
                    local_path,
                    "Response is text/html (Blocked/Challenge page)",
                )

            content = response.read()
            if (
                content.startswith(b"<")
                or content.startswith(b"<!DOCTYPE")
                or content.startswith(b"<html")
            ):
                return (
                    False,
                    url,
                    local_path,
                    "Response content is HTML text (Blocked/Challenge page)",
                )

            with open(local_path, "wb") as out_file:
                out_file.write(content)
        return True, url, local_path, None
    except Exception as e:
        return False, url, local_path, str(e)


def download_file_with_fallback(url, local_path, timeout=10, retries=3):
    """Tries to download the file from the original URL, falling back to Wayback Machine if it fails.
    Uses exponential backoff on connection errors to respect rate limits."""
    # Step 1: Try original URL
    success, dl_url, path, err = download_file(url, local_path, timeout)
    if success:
        return success, dl_url, path, err

    # Step 2: Lookup Wayback Machine URL
    wayback_url = get_wayback_url(url, timeout)
    if not wayback_url:
        return False, url, path, f"Primary failed ({err}) and not archived on Wayback"

    # Step 3: Try Wayback URL with retries + exponential backoff
    for attempt in range(1, retries + 1):
        success, wb_dl_url, path, wb_err = download_file(
            wayback_url, local_path, timeout
        )
        if success:
            return True, wayback_url, path, "Downloaded from Wayback"
        # Connection refused or reset means rate-limited — back off
        if (
            "Connection refused" in wb_err
            or "Connection reset" in wb_err
            or "timed out" in wb_err
        ):
            wait = 2**attempt  # 2s, 4s, 8s
            time.sleep(wait)
        else:
            break  # Non-retryable error (e.g. HTML response)

    return False, wayback_url, path, f"Wayback failed after {retries} retries: {wb_err}"


def main():
    parser = argparse.ArgumentParser(
        description="Extract WordPress XML data and download media."
    )
    parser.add_argument(
        "xml_files",
        nargs="*",
        help="Paths to WordPress XML export files. If empty, all XML files in the current folder will be processed.",
    )
    parser.add_argument(
        "--skip-media", action="store_true", help="Skip downloading media files."
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=3,
        help="Number of download threads (default: 3 to respect Wayback rate limits).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Download timeout in seconds (default: 15).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Retry attempts for Wayback Machine downloads (default: 3).",
    )
    args = parser.parse_args()

    # Find XML files
    xml_paths = args.xml_files
    if not xml_paths:
        xml_paths = [f for f in os.listdir(".") if f.lower().endswith(".xml")]

    if not xml_paths:
        print("No XML files found to process.")
        return

    print(f"Found XML files to parse: {xml_paths}")

    # Aggregated structures (deduplicated)
    authors = {}
    categories = {}
    tags = {}
    terms = {}
    items_by_type = {}

    processed_post_ids = set()

    for xml_path in xml_paths:
        print(f"Parsing: {xml_path}...")
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except Exception as e:
            print(f"Error parsing XML file {xml_path}: {e}")
            continue

        # Extract Authors
        for author_el in root.findall(".//wp:author", NAMESPACES):
            author_id_str = get_element_text(author_el, "wp:author_id", NAMESPACES)
            if not author_id_str:
                continue
            author_id = int(author_id_str)
            author_data = {
                "author_id": author_id,
                "author_login": get_element_text(
                    author_el, "wp:author_login", NAMESPACES
                ),
                "author_email": get_element_text(
                    author_el, "wp:author_email", NAMESPACES
                ),
                "author_display_name": get_element_text(
                    author_el, "wp:author_display_name", NAMESPACES
                ),
                "author_first_name": get_element_text(
                    author_el, "wp:author_first_name", NAMESPACES
                ),
                "author_last_name": get_element_text(
                    author_el, "wp:author_last_name", NAMESPACES
                ),
            }
            authors[author_id] = author_data

        # Extract Categories
        for cat_el in root.findall(".//wp:category", NAMESPACES):
            term_id_str = get_element_text(cat_el, "wp:term_id", NAMESPACES)
            if not term_id_str:
                continue
            term_id = int(term_id_str)
            categories[term_id] = {
                "term_id": term_id,
                "slug": get_element_text(cat_el, "wp:category_nicename", NAMESPACES),
                "parent": get_element_text(cat_el, "wp:category_parent", NAMESPACES),
                "name": get_element_text(cat_el, "wp:cat_name", NAMESPACES),
            }

        # Extract Tags
        for tag_el in root.findall(".//wp:tag", NAMESPACES):
            term_id_str = get_element_text(tag_el, "wp:term_id", NAMESPACES)
            if not term_id_str:
                continue
            term_id = int(term_id_str)
            tags[term_id] = {
                "term_id": term_id,
                "slug": get_element_text(tag_el, "wp:tag_slug", NAMESPACES),
                "name": get_element_text(tag_el, "wp:tag_name", NAMESPACES),
            }

        # Extract Terms (Custom taxonomies)
        for term_el in root.findall(".//wp:term", NAMESPACES):
            term_id_str = get_element_text(term_el, "wp:term_id", NAMESPACES)
            if not term_id_str:
                continue
            term_id = int(term_id_str)
            taxonomy = get_element_text(term_el, "wp:term_taxonomy", NAMESPACES)
            terms[(term_id, taxonomy)] = {
                "term_id": term_id,
                "taxonomy": taxonomy,
                "slug": get_element_text(term_el, "wp:term_slug", NAMESPACES),
                "parent": get_element_text(term_el, "wp:term_parent", NAMESPACES),
                "name": get_element_text(term_el, "wp:term_name", NAMESPACES),
                "description": get_element_text(
                    term_el, "wp:term_description", NAMESPACES
                ),
            }

        # Extract Items (posts, pages, attachments, nav menu items, etc.)
        for item_el in root.findall(".//item"):
            # Parse XML fields
            item_data = parse_item(item_el, NAMESPACES)
            post_id = item_data["post_id"]
            post_type = item_data["post_type"] or "post"

            # Deduplicate by post_id
            if post_id > 0:
                if post_id in processed_post_ids:
                    continue
                processed_post_ids.add(post_id)

            if post_type not in items_by_type:
                items_by_type[post_type] = []
            items_by_type[post_type].append(item_data)

    # Save authors, categories, tags, terms to JSON
    if authors:
        with open("authors.json", "w", encoding="utf-8") as f:
            json.dump(list(authors.values()), f, indent=2, ensure_ascii=False)
        print(f"Saved {len(authors)} authors to authors.json")

    if categories:
        with open("categories.json", "w", encoding="utf-8") as f:
            json.dump(list(categories.values()), f, indent=2, ensure_ascii=False)
        print(f"Saved {len(categories)} categories to categories.json")

    if tags:
        with open("tags.json", "w", encoding="utf-8") as f:
            json.dump(list(tags.values()), f, indent=2, ensure_ascii=False)
        print(f"Saved {len(tags)} tags to tags.json")

    if terms:
        with open("terms.json", "w", encoding="utf-8") as f:
            json.dump([v for v in terms.values()], f, indent=2, ensure_ascii=False)
        print(f"Saved {len(terms)} custom taxonomy terms to terms.json")

    # Save grouped items to JSON files
    for post_type, items in items_by_type.items():
        # Pluralize filename cleanly
        plural_name = post_type
        if not post_type.endswith("s"):
            if post_type.endswith("y"):
                plural_name = post_type[:-1] + "ies"
            else:
                plural_name = post_type + "s"

        filename = f"{plural_name.replace(' ', '_').replace('-', '_')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(items)} items of type '{post_type}' to {filename}")

    # Media Downloader Section
    if args.skip_media:
        print("Skipping media downloads as requested by --skip-media.")
        return

    attachments = items_by_type.get("attachment", [])
    if not attachments:
        print("No attachments found to download.")
        return

    print(
        f"Preparing to download {len(attachments)} attachments using {args.threads} threads..."
    )

    download_tasks = []
    for att in attachments:
        url = att.get("attachment_url") or att.get("guid")
        if not url:
            continue

        # Determine local path
        # Try to use relative path in _wp_attached_file postmeta
        rel_path = att.get("postmeta", {}).get("_wp_attached_file")
        if not rel_path:
            # Fallback to last part of the URL path
            parsed_url = urllib.parse.urlparse(url)
            rel_path = os.path.basename(parsed_url.path)

        if not rel_path:
            continue

        # Keep lists/tuples of _wp_attached_file if aggregate happened, use the first one
        if isinstance(rel_path, list):
            rel_path = rel_path[0]

        filename = os.path.basename(rel_path)
        dir_part = os.path.dirname(rel_path)
        prefix = dir_part.replace("/", "_").replace("\\", "_") if dir_part else ""

        # Check for filename collisions
        local_path = os.path.join("media", filename)
        # If the file already exists on disk (and has a different size or path prefix),
        # or if we have another task with the same filename but different URL, use prefix
        if os.path.exists(local_path) and prefix:
            # Check if it was one of our prefixed files
            local_path = os.path.join("media", f"{prefix}_{filename}")

        download_tasks.append((url, local_path))

    # Concurrently download attachments
    success_count = 0
    fail_count = 0
    exist_count = 0

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {
            executor.submit(
                download_file_with_fallback,
                task[0],
                task[1],
                args.timeout,
                args.retries,
            ): task
            for task in download_tasks
        }
        for i, future in enumerate(as_completed(futures), 1):
            success, url, path, err = future.result()
            if success:
                if err == "Already Exists":
                    exist_count += 1
                elif err == "Downloaded from Wayback":
                    success_count += 1
                    print(
                        f"[{i}/{len(download_tasks)}] [Success] Downloaded {path} from Wayback Machine"
                    )
                else:
                    success_count += 1
                    print(f"[{i}/{len(download_tasks)}] [Success] Downloaded {path}")
            else:
                fail_count += 1
                print(
                    f"[{i}/{len(download_tasks)}] [Failed] {url} -> {path} (Error: {err})"
                )

    print("\nMedia Download Summary:")
    print(f"  - Total processed: {len(download_tasks)}")
    print(f"  - Successfully downloaded: {success_count}")
    print(f"  - Already existed locally: {exist_count}")
    print(f"  - Failed downloads: {fail_count}")


if __name__ == "__main__":
    main()
