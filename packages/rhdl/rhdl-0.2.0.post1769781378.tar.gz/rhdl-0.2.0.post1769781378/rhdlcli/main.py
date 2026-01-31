#!/usr/bin/env python
# -*- coding: utf-8 -*-
import functools
import os
import sys

from rhdlcli.cli import parse_arguments
from rhdlcli.compose import list_compose_versions
from rhdlcli.downloader import download_component
from rhdlcli.pull_secret import download_pull_secret
from rhdlcli.options import build_options, login
from rhdlcli.validator import (
    exit_if_credentials_invalid,
    validate_options,
)


def catch_all_and_print(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyboardInterrupt:
            print("Keyboard interrupt exiting...")
            sys.exit(130)
        except Exception as e:
            print(e)
            sys.exit(1)

    return inner


@catch_all_and_print
def run_rhdl(argv, cwd, env_variables):
    arguments = parse_arguments(argv[1:], cwd)
    options = build_options(arguments, env_variables)
    if options["command"] == "login":
        login(options)
        return
    exit_if_credentials_invalid(options)
    if options["command"] == "download-pull-secret":
        download_pull_secret(options)
        return
    if options["command"] == "version-list":
        list_compose_versions(options)
        return
    validate_options(options)
    download_component(options)


def main():
    arguments = sys.argv
    cwd = os.path.realpath(os.getcwd())
    env_variables = dict(os.environ)
    run_rhdl(arguments, cwd, env_variables)


if __name__ == "__main__":
    main()
