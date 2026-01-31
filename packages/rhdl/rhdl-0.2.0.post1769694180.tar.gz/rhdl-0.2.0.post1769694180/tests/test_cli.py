import pytest

from rhdlcli.cli import parse_arguments


def test_parse_arguments_command_argument():
    assert parse_arguments(["login"])["command"] == "login"
    assert parse_arguments(["download", "RHEL-9.4"])["command"] == "download"
    assert (
        parse_arguments(["download-pull-secret"])["command"] == "download-pull-secret"
    )


def test_parse_arguments_download_command_no_options():
    args = parse_arguments(["download", "RHEL-9.4"], "/home/dci")
    assert args["destination"] == "/home/dci/RHEL-9.4"
    assert args["tags"] == []
    assert args["channel"] == "milestone"
    assert args["compose"] == "RHEL-9.4"
    assert args["include_and_exclude"] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]


def test_parse_arguments_download_command_custom_destination():
    args = parse_arguments(["download", "RHEL-9.4", "-d", "/tmp/d1"])
    assert args["destination"] == "/tmp/d1/RHEL-9.4"

    args = parse_arguments(["download", "RHEL-9.4", "--destination", "/tmp/d2"])
    assert args["destination"] == "/tmp/d2/RHEL-9.4"

    cwd = "/tmp"
    args = parse_arguments(
        ["download", "RHEL-9.4", "-d", "../home/rhdl", "-t", "nightly"], cwd
    )
    assert args["destination"] == "/home/rhdl/RHEL-9.4"


def test_parse_arguments_download_command_tags():
    assert parse_arguments(["download", "RHEL-9.4", "-t", "5.14.0-570.79.1.el9_6"])[
        "tags"
    ] == ["5.14.0-570.79.1.el9_6"]
    assert parse_arguments(["download", "RHEL-9.4", "--tag", "5.14.0-570.79.1.el9_6"])[
        "tags"
    ] == ["5.14.0-570.79.1.el9_6"]
    assert parse_arguments(["download", "RHEL-9.4", "-t", "tag1,tag2"])["tags"] == [
        "tag1",
        "tag2",
    ]
    assert parse_arguments(["download", "RHEL-9.4", "--tag", "tag1,tag2"])["tags"] == [
        "tag1",
        "tag2",
    ]
    assert parse_arguments(["download", "RHEL-9.4", "-t", "tag1", "-t", "tag2"])[
        "tags"
    ] == ["tag1", "tag2"]
    assert parse_arguments(["download", "RHEL-9.4", "--tag", "tag1", "--tag", "tag2"])[
        "tags"
    ] == ["tag1", "tag2"]
    assert parse_arguments(
        ["download", "RHEL-9.4", "--tag", "tag1", "--channel", "nightly"]
    )["tags"] == ["tag1"]


def test_parse_arguments_with_channel_flags():
    assert (
        parse_arguments(["download", "RHEL-10", "--channel", "nightly"])["channel"]
        == "nightly"
    )
    assert (
        parse_arguments(["download", "RHEL-10", "--channel", "candidate"])["channel"]
        == "candidate"
    )
    assert (
        parse_arguments(["download", "RHEL-10", "--channel", "milestone"])["channel"]
        == "milestone"
    )
    assert (
        parse_arguments(["download", "RHEL-10", "--channel", "unknown"])["channel"]
        is None
    )


def test_nrt_tags_channel_backward_compatibility_between_v010_and_v020():
    args = parse_arguments(["download", "RHEL-10", "--tag", "nightly"])
    channel = args["channel"]
    tags = args["tags"]
    assert channel == "nightly"
    assert tags == []

    args = parse_arguments(["download", "RHEL-10", "--tag", "candidate"])
    channel = args["channel"]
    tags = args["tags"]
    assert channel == "candidate"
    assert tags == []

    args = parse_arguments(["download", "RHEL-10", "--tag", "milestone"])
    channel = args["channel"]
    tags = args["tags"]
    assert channel == "milestone"
    assert tags == []


def test_parse_arguments_download_command_include_and_exclude_in_order():
    assert parse_arguments(
        [
            "download",
            "RHEL-9.4",
            "-i",
            "AppStream/x86_64/os/*",
            "--exclude",
            "*/aarch64/*",
            "--include",
            "BaseOS/x86_64/os/*",
            "--exclude",
            "*",
        ]
    )["include_and_exclude"] == [
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "*/aarch64/*", "type": "exclude"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]


def test_parse_arguments_allow_comma_separated_pattern():
    assert parse_arguments(
        [
            "download",
            "RHEL-9.4",
            "--include",
            "AppStream/x86_64/os/*, BaseOS/x86_64/os/*",
            "--exclude",
            "BaseOS/x86_64/debug/*,AppStream/x86_64/debug/*",
        ]
    )["include_and_exclude"] == [
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/debug/*", "type": "exclude"},
        {"pattern": "AppStream/x86_64/debug/*", "type": "exclude"},
    ]


def test_parse_arguments_download_pull_secret_no_options():
    args = parse_arguments(["download-pull-secret"])
    assert args["destination"].endswith("/.docker/config.json")
    assert args["force"] is False
    assert args["merge"] is False


def test_parse_arguments_download_pull_secret_custom_destination():
    args = parse_arguments(
        ["download-pull-secret", "--destination", "/path/to/pull-secret.json"]
    )
    assert args["destination"] == "/path/to/pull-secret.json"

    args = parse_arguments(["download-pull-secret", "-d", "/path/to/pull-secret.json"])
    assert args["destination"] == "/path/to/pull-secret.json"


def test_parse_arguments_download_pull_secret_force():
    args = parse_arguments(["download-pull-secret", "-f"])
    assert args["force"]

    args = parse_arguments(["download-pull-secret", "--force"])
    assert args["force"]


def test_parse_arguments_download_pull_secret_merge():
    args = parse_arguments(["download-pull-secret", "-m"])
    assert args["merge"]

    args = parse_arguments(["download-pull-secret", "--merge"])
    assert args["merge"]


def test_parse_arguments_download_pull_secret_other_parameter_are_not_present():
    args = parse_arguments(["download-pull-secret"])
    assert "compose" not in args


def test_should_raise_exception_when_command_is_invalid():
    with pytest.raises(SystemExit):
        parse_arguments(["send", "RHEL-9.4"])


def test_documentation_saying_default_command_is_equivalent_to():
    assert parse_arguments(
        [
            "download",
            "RHEL-9.4",
        ]
    ) == parse_arguments(
        [
            "download",
            "RHEL-9.4",
            "--destination",
            ".",
            "--include",
            ".composeinfo",
            "--include",
            "metadata/*",
            "--include",
            "AppStream/x86_64/os/*",
            "--include",
            "BaseOS/x86_64/os/*",
            "--exclude",
            "*",
            "--channel",
            "milestone",
        ]
    )


def test_with_flat_and_no_destination_should_download_in_current_directory():
    cwd = "/home/dci"
    args = parse_arguments(["download", "RHEL-9.4", "--flat"], cwd)
    assert args["destination"] == "/home/dci"
    assert args["flat"]


def test_with_flat_and_custom_destination_should_download_directly_in_destination():
    args = parse_arguments(["download", "RHEL-9.4", "--flat", "-d", "/tmp/repo"])
    assert args["destination"] == "/tmp/repo"
    assert args["flat"]


def test_parse_arguments_creates_subdirectory_by_default():
    cwd = "/home/user"
    args = parse_arguments(["download", "RHEL-10"], cwd)
    assert args["destination"] == "/home/user/RHEL-10"
    assert args["flat"] is False

    args = parse_arguments(["download", "RHEL-10", "-d", "repos"], cwd)
    assert args["destination"] == "/home/user/repos/RHEL-10"
    assert args["flat"] is False

    args = parse_arguments(["download", "RHEL-10", "-d", "/opt/mirrors"], cwd)
    assert args["destination"] == "/opt/mirrors/RHEL-10"
    assert args["flat"] is False


def test_parse_arguments_force_flag():
    args = parse_arguments(["download", "RHEL-10"])
    assert args["force"] is False

    args = parse_arguments(["download", "RHEL-10", "--force"])
    assert args["force"] is True

    args = parse_arguments(["download", "RHEL-10", "-f"])
    assert args["force"] is True


def test_parse_arguments_with_arch_flags():
    assert parse_arguments(["download", "RHEL-10", "--arch", "x86_64"])["archs"] == [
        "x86_64"
    ]
    assert parse_arguments(["download", "RHEL-10", "--arch", "x86_64"])[
        "include_and_exclude"
    ] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]

    assert parse_arguments(["download", "RHEL-10", "--arch", "x86_64,ppc64le"])[
        "include_and_exclude"
    ] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "AppStream/ppc64le/os/*", "type": "include"},
        {"pattern": "BaseOS/ppc64le/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]

    assert parse_arguments(
        ["download", "RHEL-10", "--arch", "x86_64", "--arch", "ppc64le"]
    )["include_and_exclude"] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "AppStream/ppc64le/os/*", "type": "include"},
        {"pattern": "BaseOS/ppc64le/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]

    assert parse_arguments(["download", "RHEL-10", "--arch", "ppc64le,x86_64"])[
        "include_and_exclude"
    ] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/ppc64le/os/*", "type": "include"},
        {"pattern": "BaseOS/ppc64le/os/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]


def test_parse_arguments_with_variant_flags():
    assert parse_arguments(["download", "RHEL-10", "--variant", "AppStream"])[
        "include_and_exclude"
    ] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]

    assert parse_arguments(["download", "RHEL-10", "--variant", "AppStream,BaseOS"])[
        "include_and_exclude"
    ] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]

    assert parse_arguments(
        ["download", "RHEL-10", "--variant", "AppStream", "--variant", "RT"]
    )["include_and_exclude"] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "RT/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]

    assert parse_arguments(["download", "RHEL-10", "--variant", "RT,AppStream"])[
        "include_and_exclude"
    ] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "RT/x86_64/os/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]


def test_parse_arguments_with_variant_flags_case_insensitive():
    assert parse_arguments(["download", "RHEL-10", "--variant", "appstream"])[
        "include_and_exclude"
    ] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]


def test_parse_arguments_with_debug_symbols():
    assert parse_arguments(["download", "RHEL-10", "--with-debug-symbols"])[
        "with_debug_symbols"
    ]
    assert parse_arguments(["download", "RHEL-10", "--with-debug"])[
        "with_debug_symbols"
    ]
    assert parse_arguments(["download", "RHEL-10", "--with-debug"])[
        "include_and_exclude"
    ] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "AppStream/x86_64/debug/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/debug/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]


def test_parse_arguments_with_source():
    assert parse_arguments(["download", "RHEL-10", "--with-source"])["with_source"]
    assert parse_arguments(["download", "RHEL-10", "--with-source"])[
        "include_and_exclude"
    ] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "AppStream/source/tree/*", "type": "include"},
        {"pattern": "BaseOS/source/tree/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]


def test_parse_arguments_with_multiple_fields():
    assert parse_arguments(
        [
            "download",
            "RHEL-10",
            "--arch",
            "ppc64le",
            "--variant",
            "AppStream",
            "--with-debug-symbols",
            "--with-source",
        ]
    )["include_and_exclude"] == [
        {"pattern": ".composeinfo", "type": "include"},
        {"pattern": "metadata/*", "type": "include"},
        {"pattern": "AppStream/ppc64le/os/*", "type": "include"},
        {"pattern": "AppStream/ppc64le/debug/*", "type": "include"},
        {"pattern": "AppStream/source/tree/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]
