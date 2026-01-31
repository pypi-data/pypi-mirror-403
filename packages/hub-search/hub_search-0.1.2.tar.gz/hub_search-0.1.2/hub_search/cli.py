import argparse
from hub_search.search import run_search
from hub_search.clean import run_clean
from hub_search.verify import run_verify
from hub_search.task import run_task

def main():
    parser = argparse.ArgumentParser(description="Hub Search - GitHub Privacy Search & Validation Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: search
    parser_search = subparsers.add_parser("search", help="Search GitHub for code.")
    parser_search.add_argument("query", help="The search query.")
    parser_search.add_argument("--limit", type=int, default=30, help="Results limit.")
    parser_search.add_argument("--regex", help="Optional regex for local filtering.")
    parser_search.add_argument("--enum", action="store_true", help="Enable enumeration mode.")

    # Command: clean
    parser_clean = subparsers.add_parser("clean", help="Extract keys from raw search results.")
    parser_clean.add_argument("input_dir", help="Directory containing search results.")
    parser_clean.add_argument("output_file", help="File to save extracted keys.")

    # Command: verify
    parser_verify = subparsers.add_parser("verify", help="Verify validity of extracted keys.")
    parser_verify.add_argument("input_file", help="File containing keys to verify.")
    parser_verify.add_argument("--output-dir", help="Output directory for valid keys (defaults to current dir).")
    parser_verify.add_argument("--threads", type=int, default=5, help="Number of concurrent threads.")
    parser_verify.add_argument("--prompt-file", help="Optional file with custom prompt content.")

    # Command: task
    parser_task = subparsers.add_parser("task", help="Run a full automated task (Search -> Clean -> Verify).")
    parser_task.add_argument("query", help="The search query (automatically runs in enum mode).")
    parser_task.add_argument("--cwd", help="Optional working directory (defaults to current).")
    parser_task.add_argument("--limit", type=int, default=30, help="Search limit per query.")
    parser_task.add_argument("--threads", type=int, default=5, help="Verification threads.")

    args = parser.parse_args()

    if args.command == "search":
        run_search(args.query, args.limit, args.regex, args.enum)
    elif args.command == "clean":
        run_clean(args.input_dir, args.output_file)
    elif args.command == "verify":
        run_verify(args.input_file, args.output_dir, args.threads, args.prompt_file)
    elif args.command == "task":
        run_task(args.query, args.cwd, args.limit, args.threads)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
