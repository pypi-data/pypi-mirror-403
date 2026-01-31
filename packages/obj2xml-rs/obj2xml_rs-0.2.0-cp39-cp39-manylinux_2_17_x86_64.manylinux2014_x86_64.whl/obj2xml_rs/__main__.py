import sys
import json
import argparse
import logging
from typing import Any, Iterable

from . import unparse, parse

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("obj2xml-rs")


def json_stream_generator(fp) -> Iterable[Any]:
    """
    Reads a JSON file containing a list or stream of objects
    and yields them one by one.
    """
    try:
        data = json.load(fp)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        sys.exit(1)

    if isinstance(data, list):
        yield from data
    else:
        yield data


def handle_unparse(args):
    """Logic for JSON -> XML conversion"""
    if args.input_file.isatty():
        print("Error: No input provided for unparse.")
        sys.exit(1)

    if args.stream:
        # If streaming, we treat input as an iterable generator
        data_source = json_stream_generator(args.input_file)
    else:
        try:
            data_source = json.load(args.input_file)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
            sys.exit(1)
    # If output path is given, we pass the path string to Rust
    # If not, we pass sys.stdout.buffer (binary stream) or let Rust return a string
    output_target = args.output
    # If streaming to stdout, pass the buffer
    if args.stream and output_target is None:
        output_target = sys.stdout.buffer
    try:
        result = unparse(
            data_source,
            output=output_target,
            pretty=args.pretty,
            indent=args.indent,
            encoding=args.encoding,
            full_document=not args.no_full_document,
            compat=args.compat,
            attr_prefix=args.attr_prefix,
            cdata_key=args.cdata_key,
            item_name=args.item_name,
            sort_attributes=args.root_attrs,
            streaming=args.stream,
        )
        if args.output is None and not args.stream:
            print(result)
    except Exception as e:
        logger.error(f"Unparse failed: {e}")
        sys.exit(1)


def handle_parse(args):
    """Logic for XML -> JSON conversion"""
    if args.input_file.isatty():
        print("Error: No input provided for parse.")
        sys.exit(1)

    # Read XML content
    # Note: For very large files, we might want to pass the file object directly,
    # but argparse opens in text mode by default.
    # The rust library handles strings or bytes.
    xml_content = args.input_file.read()

    try:
        result = parse(
            xml_content,
            encoding=args.encoding,
            attr_prefix=args.attr_prefix,
            cdata_key=args.cdata_key,
            force_cdata=args.force_cdata,
            process_namespaces=args.process_namespaces,
            namespace_separator=args.namespace_separator,
            strip_whitespace=not args.no_strip_whitespace,
            force_list=args.force_list,
            process_comments=args.comments,
        )

        # Output JSON
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2 if args.pretty else None)
        else:
            print(json.dumps(result, indent=2 if args.pretty else None))

    except Exception as e:
        logger.error(f"Parse failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="obj2xml_rs",
        description="High-performance XML <-> Dictionary converter using Rust.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True
    parser_un = subparsers.add_parser("unparse", help="Convert JSON/Dict to XML")
    parser_un.add_argument(
        "input_file",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="Input JSON file",
    )
    parser_un.add_argument("-o", "--output", type=str, help="Output XML file path")

    parser_un.add_argument("--pretty", action="store_true", help="Indent output")
    parser_un.add_argument("--indent", default="  ", help="Indentation string")
    parser_un.add_argument("--encoding", default="utf-8", help="XML encoding")
    parser_un.add_argument(
        "--no-full-document", action="store_true", help="Omit XML declaration"
    )
    parser_un.add_argument("--compat", choices=["native", "legacy"], default="native")
    parser_un.add_argument("--root-attrs", action="store_true", help="Sort attributes")
    parser_un.add_argument("--attr-prefix", default="@")
    parser_un.add_argument("--cdata-key", default="#text")
    parser_un.add_argument("--item-name", default="item", help="Tag for list items")
    parser_un.add_argument(
        "--stream", action="store_true", help="Enable streaming (low memory)"
    )
    parser_un.set_defaults(func=handle_unparse)

    parser_p = subparsers.add_parser("parse", help="Convert XML to JSON/Dict")
    parser_p.add_argument(
        "input_file",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="Input XML file",
    )
    parser_p.add_argument("-o", "--output", type=str, help="Output JSON file path")
    parser_p.add_argument("--pretty", action="store_true", help="Indent JSON output")
    parser_p.add_argument("--encoding", default="utf-8", help="Input XML encoding hint")
    parser_p.add_argument("--attr-prefix", default="@")
    parser_p.add_argument("--cdata-key", default="#text")
    parser_p.add_argument(
        "--force-cdata",
        action="store_true",
        help="Always use #text key even for simple nodes",
    )
    parser_p.add_argument(
        "--process-namespaces",
        action="store_true",
        help="Expand namespaces (ns:tag -> http://uri:tag)",
    )
    parser_p.add_argument(
        "--namespace-separator", default=":", help="Separator for expanded namespaces"
    )
    parser_p.add_argument(
        "--no-strip-whitespace",
        action="store_true",
        help="Keep leading/trailing whitespace",
    )
    parser_p.add_argument(
        "--comments", action="store_true", help="Include comments in output"
    )
    parser_p.add_argument(
        "--force-list", nargs="+", help="Tags to always parse as lists", default=None
    )
    parser_p.set_defaults(func=handle_parse)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
