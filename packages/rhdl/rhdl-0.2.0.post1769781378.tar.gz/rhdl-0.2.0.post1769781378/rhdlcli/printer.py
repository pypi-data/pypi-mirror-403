#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys
from tabulate import tabulate


def _extract_rows_and_headers(data, keys_headers):
    headers = list(keys_headers.values())
    rows = [[row.get(key) for key in keys_headers.keys()] for row in data]
    return rows, headers


def print_output(data, headers, options):
    format = options.get("format")
    if format == "json":
        json.dump(data, sys.stdout, indent=2)
        print()
    else:
        tabulate_data, tabulate_headers = _extract_rows_and_headers(data, headers)
        print(tabulate(tabulate_data, headers=tabulate_headers, tablefmt=format))
