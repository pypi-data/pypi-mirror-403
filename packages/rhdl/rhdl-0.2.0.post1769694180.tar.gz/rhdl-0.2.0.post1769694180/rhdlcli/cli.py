#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import pathlib

from rhdlcli.version import __version__

DESCRIPTION = "RHDL CLI - Download the latest RHEL compose easily."

COPYRIGHT = """
Copyright © 2026 Red Hat.
Licensed under the Apache License, Version 2.0
"""

DEFAULT_VARIANTS = ["AppStream", "BaseOS"]
AVAILABLE_VARIANTS = [
    "AppStream",
    "BaseOS",
    "CRB",
    "HighAvailability",
    "NFV",
    "RT",
    "SAP",
    "SAPHANA",
    "metadata",
    "unified",
]
DEFAULT_ARCHS = ["x86_64"]
DEFAULT_CONTENT_TYPES = ["os"]
AVAILABLE_CHANNELS = ["nightly", "candidate", "milestone"]


def _build_default_include_exclude_list(args_dict):
    archs = args_dict["archs"]
    variants = args_dict["variants"]
    content_types = args_dict["content_types"]
    default_include_exclude_list = [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
    ]
    for arch in archs:
        for variant in variants:
            for content_type in content_types:
                default_include_exclude_list.append(
                    {
                        "pattern": f"{variant}/{arch}/{content_type}/*",
                        "type": "include",
                    },
                )
    if args_dict["with_source"]:
        for variant in variants:
            default_include_exclude_list.append(
                {
                    "pattern": f"{variant}/source/tree/*",
                    "type": "include",
                },
            )
    default_include_exclude_list.append(
        {"pattern": "*", "type": "exclude"},
    )
    return default_include_exclude_list


def _get_default_archs(args_dict):
    return args_dict.pop("archs", None) or DEFAULT_ARCHS


def _validate_channel(args_dict):
    channel = args_dict.get("channel")
    if channel and channel not in AVAILABLE_CHANNELS:
        return None
    return channel


def _get_default_tags_and_channel(args_dict):
    channel = _validate_channel(args_dict)
    tags = args_dict.pop("tags", None)
    tags = tags if tags else []
    tags_without_channel = []
    for tag in tags:
        if tag in AVAILABLE_CHANNELS:
            channel = tag
        else:
            tags_without_channel.append(tag)
    return tags_without_channel, channel


def _get_default_variants(args_dict):
    variants = args_dict.pop("variants", None) or DEFAULT_VARIANTS
    variant_names_with_lower_keys = {v.lower(): v for v in AVAILABLE_VARIANTS}
    cleaned_variants = []
    for variant in variants:
        lowercase_variant = variant.lower()
        if lowercase_variant in variant_names_with_lower_keys:
            cleaned_variants.append(variant_names_with_lower_keys[lowercase_variant])
    return cleaned_variants


def _get_content_types(args_dict):
    if args_dict.get("with_debug_symbols", False):
        return ["os", "debug"]
    return DEFAULT_CONTENT_TYPES


def clean_with_default_values(parsed_arguments, cwd):
    args_dict = vars(parsed_arguments)

    if args_dict.get("command") == "download":
        args_dict["archs"] = _get_default_archs(args_dict)
        args_dict["variants"] = _get_default_variants(args_dict)
        tags, channel = _get_default_tags_and_channel(args_dict)
        args_dict["tags"] = tags
        args_dict["channel"] = channel
        args_dict["content_types"] = _get_content_types(args_dict)
        if "include_and_exclude" not in args_dict:
            args_dict["include_and_exclude"] = _build_default_include_exclude_list(
                args_dict
            )

        if "include" in args_dict:
            del args_dict["include"]
        if "exclude" in args_dict:
            del args_dict["exclude"]

        if args_dict.get("destination") is None:
            base_path = pathlib.Path(cwd)
        else:
            base_path = pathlib.Path(cwd, args_dict["destination"]).resolve()

        if not args_dict["flat"]:
            base_path = base_path / args_dict["compose"]

        args_dict["destination"] = os.fspath(base_path)

    return args_dict


class IncludeExcludeAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not hasattr(namespace, "include_and_exclude"):
            setattr(namespace, "include_and_exclude", [])
        namespace.include_and_exclude.extend(
            {"pattern": value.strip(), "type": self.dest}
            for value in values.split(",")
            if value.strip()
        )


class CommaSeparatedListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        items = [] if items is None else list(items)
        items.extend(v.strip() for v in values.split(",") if v.strip())
        setattr(namespace, self.dest, items)


def add_login_command(subparsers):
    """Add the login subcommand"""
    login_parser = subparsers.add_parser(
        "login",
        help="Login to RHDL",
        description="Authenticate with RHDL to access compose downloads.",
        epilog=COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    login_parser.set_defaults(command="login")


def add_download_command(subparsers):
    """Add the download subcommand"""
    download_examples = """
examples:
  # Download latest RHEL-10 compose in <cwd>/RHEL-10 folder
  rhdl download RHEL-10

  # Download latest RHEL-10 in /tmp/repo/RHEL-10 folder
  rhdl download RHEL-10 --destination /tmp/repo

  # Download directly in /tmp/repo without creating RHEL-10 subdirectory
  rhdl download RHEL-10 --destination /tmp/repo --flat

  # Download specific architecture
  rhdl download RHEL-10 --arch aarch64

  # Download multiple architectures
  rhdl download RHEL-10 --arch x86_64,aarch64

  # Download specific variant
  rhdl download RHEL-10 --variant AppStream

  # Download multiple variants
  rhdl download RHEL-10 --variant AppStream,BaseOS,CRB

  # Download with debug symbols
  rhdl download RHEL-10 --with-debug

  # Download with source RPMs
  rhdl download RHEL-10 --with-source

  # Download with custom include/exclude patterns
  rhdl download RHEL-10 --include "*/x86_64/*" --exclude "*/debug/*"

  # Download with regex patterns (using | for alternation)
  rhdl download RHEL-9.4 --include "(AppStream|BaseOS)/(x86_64|s390x)/os/Packages/*" --exclude "*"

  # Download with comma-separated patterns
  rhdl download RHEL-9.4 --include "AppStream/x86_64/os/*,BaseOS/x86_64/os/*" --exclude "*"

  # Download specific tags
  rhdl download RHEL-10 --tag kernel:6.12.0-55.54.1.el10_0
"""
    download_parser = subparsers.add_parser(
        "download",
        help="Download a RHEL compose",
        description="Download a specific RHEL compose with filtering options.",
        epilog=download_examples + COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    download_parser.add_argument(
        "compose", metavar="COMPOSE", help="Compose ID or NAME (e.g., RHEL-10)"
    )
    download_parser.add_argument(
        "-d",
        "--destination",
        metavar="DESTINATION",
        help="Destination folder where a <COMPOSE> subdirectory will be created (default: current directory)",
    )
    download_parser.add_argument(
        "--flat",
        action="store_true",
        default=False,
        help="Download directly into destination folder without creating a subdirectory with the Compose ID",
    )
    download_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force download even if destination folder already exists",
    )
    download_parser.add_argument(
        "--arch",
        action=CommaSeparatedListAction,
        metavar="ARCH",
        dest="archs",
        help=f"download a specific architecture (default: {','.join(DEFAULT_ARCHS)}). Supports comma-separated values and can be used multiple times.",
    )
    download_parser.add_argument(
        "--variant",
        action=CommaSeparatedListAction,
        metavar="VARIANT",
        dest="variants",
        help=f"download a specific variant (default: {','.join(DEFAULT_VARIANTS)}). Supports comma-separated values and can be used multiple times. Available variants: {', '.join(AVAILABLE_VARIANTS)}",
    )
    download_parser.add_argument(
        "--with-debug-symbols",
        "--with-debug",
        action="store_true",
        default=False,
        dest="with_debug_symbols",
        help="Include debug symbols in the download",
    )
    download_parser.add_argument(
        "--with-source",
        action="store_true",
        default=False,
        dest="with_source",
        help="Include source tree packages in the download",
    )
    download_parser.add_argument(
        "-i",
        "--include",
        action=IncludeExcludeAction,
        metavar="PATTERN",
        dest="include",
        help="File paths pattern to download. Supports wildcards (*), regex patterns (with |, (), ), and comma-separated patterns. Can be used multiple times.",
    )
    download_parser.add_argument(
        "-e",
        "--exclude",
        action=IncludeExcludeAction,
        metavar="PATTERN",
        dest="exclude",
        help="File paths pattern to exclude. Supports wildcards (*), regex patterns (with |, (), ), and comma-separated patterns. Can be used multiple times.",
    )
    download_parser.add_argument(
        "-t",
        "--tag",
        action=CommaSeparatedListAction,
        metavar="TAG",
        dest="tags",
        help="Filter RHEL compose with tags. Supports comma-separated values and can be used multiple times.",
    )
    download_parser.add_argument(
        "--channel",
        metavar="CHANNEL",
        default="milestone",
        help=f"Filter RHEL compose with a channel (choices: {', '.join(AVAILABLE_CHANNELS)})",
    )
    download_parser.set_defaults(command="download")


def add_download_pull_secret_command(subparsers):
    """Add the download-pull-secret subcommand"""
    pull_secret_examples = """
examples:
  # Download pull-secret to default location (~/.docker/config.json)
  rhdl download-pull-secret

  # Download pull-secret to custom location
  rhdl download-pull-secret --destination ./my-pull-secret.json

  # Force overwrite existing file
  rhdl download-pull-secret --force

  # Merge with existing pull-secret
  rhdl download-pull-secret --merge
"""
    pull_secret_parser = subparsers.add_parser(
        "download-pull-secret",
        help="Download your team's pull-secret",
        description="Download the pull-secret associated with your team for authenticating to container registries.",
        epilog=pull_secret_examples + COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pull_secret_parser.add_argument(
        "-d",
        "--destination",
        metavar="PATH",
        default=os.path.expanduser("~/.docker/config.json"),
        help="Destination file path for the pull-secret (default: ~/.docker/config.json)",
    )
    pull_secret_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force overwrite if destination file already exists",
    )
    pull_secret_parser.add_argument(
        "-m",
        "--merge",
        action="store_true",
        default=False,
        help="Merge with existing pull-secret instead of replacing it",
    )
    pull_secret_parser.set_defaults(command="download-pull-secret")


def parse_arguments(arguments, cwd=None):
    cwd = cwd or os.getcwd()
    parser = argparse.ArgumentParser(
        prog="rhdl",
        description=DESCRIPTION,
        epilog=COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        help="Use 'rhdl COMMAND --help' for more information on a command",
    )

    add_login_command(subparsers)
    add_download_command(subparsers)
    add_download_pull_secret_command(subparsers)

    parsed_arguments = parser.parse_args(arguments)

    if parsed_arguments.command is None:
        parser.print_help()
        raise SystemExit(1)

    return clean_with_default_values(parsed_arguments, cwd)
