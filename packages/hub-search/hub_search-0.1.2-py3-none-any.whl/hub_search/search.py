import datetime
import os
import re
import string
import sys
import time

import requests


def search_github(query, token=None, sort="indexed", order="desc", per_page=30, page=1):
    """
    Search GitHub for a specific string using the Code Search API.
    """
    base_url = "https://api.github.com/search/code"
    headers = {"Accept": "application/vnd.github.v3+json"}

    if token:
        headers["Authorization"] = f"token {token}"
    else:
        print(
            "Warning: No GITHUB_TOKEN provided. Rate limits will be very low (10 requests/minute)."
        )

    params = {
        "q": query,
        "sort": sort,
        "order": order,
        "per_page": per_page,
        "page": page,
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(
                base_url, headers=headers, params=params, timeout=10
            )

            if response.status_code == 200:
                return response.json()

            # Handle Server Errors (5xx) -> Retry
            elif 500 <= response.status_code < 600:
                print(
                    f"[!] Server Error {response.status_code}. Retrying in {2 ** attempt}s..."
                )
                time.sleep(2**attempt)
                continue

            # Handle Rate Limit (403) -> specific check
            elif response.status_code == 403:
                # If it's a secondary rate limit (abuse detection), sometimes waiting helps.
                # But usually 403 implies we hit a hard ceiling.
                # We'll print details and stop to avoid banning.
                print(f"Error 403: Rate limit exceeded or forbidden. {response.text}")
                return None

            elif response.status_code == 422:
                print(
                    f"Error 422: Validation failed (likely query syntax). {response.text}"
                )
                return None
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"[!] Network error: {e}. Retrying in {2 ** attempt}s...")
            time.sleep(2**attempt)
            continue

    print("[!] Max retries exceeded.")
    return None


def get_file_content(url, token):
    """
    Fetch raw content of a file from GitHub using the API URL.
    """
    headers = {"Accept": "application/vnd.github.v3.raw"}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def run_search(query, limit=30, regex=None, enum=False, output_dir=None):
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        print("Error: GITHUB_TOKEN environment variable is required.")
        print("Please set it before running:")
        print("  export GITHUB_TOKEN='your_github_personal_access_token'")
        sys.exit(1)

    # Function to handle pagination logic
    def fetch_all_pages(q, max_results):
        all_items = []
        current_page = 1
        # GitHub API limit for per_page is 100
        batch_size = min(max_results, 100)

        while len(all_items) < max_results:
            # Adjust batch size for the last page if needed
            remaining = max_results - len(all_items)
            current_batch = min(remaining, 100)

            results = search_github(
                q, token=token, per_page=current_batch, page=current_page
            )

            if not results or "items" not in results:
                break

            items = results["items"]
            if not items:
                break

            all_items.extend(items)

            if len(items) < current_batch:
                # Less items returned than requested, meaning end of results
                break

            current_page += 1
            if len(all_items) < max_results:
                time.sleep(1.5)  # Sleep between pages

        return all_items, results.get("total_count", 0) if results else 0

    if enum:
        if output_dir:
            # Use provided directory, ensure it exists
            os.makedirs(output_dir, exist_ok=True)
            output_filepath = os.path.join(output_dir, "results.txt")
            print(f"Starting enumeration search mode (Task managed).")
        else:
            # Create timestamped directory
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            os.makedirs(timestamp, exist_ok=True)
            output_filepath = os.path.join(timestamp, "results.txt")
            print(f"Starting enumeration search mode.")

        print(f"Results will be saved to: {output_filepath}")

        # a-z0-9, but skip 'x' as requested
        suffixes = (string.ascii_lowercase + string.digits).replace("x", "")

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(f"Search started at {datetime.datetime.now()}\n")
            f.write(f"Base Query: {query}\n")
            f.write("=" * 60 + "\n\n")

            for char in suffixes:
                sub_query = f"{query}{char}"
                print(f"Querying: {sub_query} ...")
                f.write(f"Query: {sub_query}\n")
                f.write("-" * 20 + "\n")

                items, total_count = fetch_all_pages(sub_query, limit)

                f.write(f"Found {total_count} matches (fetched top {len(items)}):\n")

                if len(items) == 0:
                    f.write("  No results.\n")

                for item in items:
                    repo_name = item.get("repository", {}).get(
                        "full_name", "Unknown Repo"
                    )
                    file_path = item.get("path", "Unknown Path")
                    api_url = item.get("url")

                    f.write(f"  [-] Repo: {repo_name}\n")
                    f.write(f"      File: {file_path}\n")

                    if api_url:
                        content = get_file_content(api_url, token)
                        if content:
                            f.write("      Content:\n")
                            f.write("      " + "=" * 10 + " START " + "=" * 10 + "\n")
                            for line in content.splitlines():
                                f.write(f"      {line}\n")
                            f.write("      " + "=" * 10 + "  END  " + "=" * 10 + "\n")
                        else:
                            f.write("      [!] Could not fetch content.\n")

                    f.write("\n" + "-" * 40 + "\n")

                f.write("\n")
                time.sleep(2.1)

        print(f"\nEnumeration search complete. Check {output_filepath}")
        return

    # Default single query behavior
    print(f"Searching GitHub for: '{query}'...")

    items, total_count = fetch_all_pages(query, limit)

    if items:
        print(
            f"\nFound approx {total_count} results via API. Processing top {len(items)} for detailed check...\n"
        )

        found_matches = False

        for item in items:
            repo_name = item.get("repository", {}).get("full_name", "Unknown Repo")
            file_path = item.get("path", "Unknown Path")
            html_url = item.get("html_url", "#")
            api_url = item.get("url")

            if regex:
                if not api_url:
                    continue

                content = get_file_content(api_url, token)
                if content:
                    matches = re.findall(regex, content)
                    if matches:
                        found_matches = True
                        print(f"[*] MATCH FOUND in {repo_name}")
                        print(f"    File: {file_path}")
                        print(f"    Link: {html_url}")
                        print(f"    Matches: {matches}")
                        print("-" * 40)
            else:
                found_matches = True
                print(f"[-] Repo: {repo_name}")
                print(f"    File: {file_path}")
                print(f"    Link: {html_url}")
                print("-" * 40)

        if not found_matches:
            if regex:
                print("No files matched the provided regex within the search results.")
            else:
                print("No results found.")

    else:
        print("No items found.")
