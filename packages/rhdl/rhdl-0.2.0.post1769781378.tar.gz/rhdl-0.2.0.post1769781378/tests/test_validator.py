import os
import tempfile
import pytest

from rhdlcli.validator import (
    credentials_are_defined,
    destination_folder_exists,
    exit_if_destination_exists,
    exit_if_variants_are_unknown,
    exit_if_channel_is_unknown,
)


def test_credentials_are_defined():
    assert credentials_are_defined(options={}) is False
    assert (
        credentials_are_defined(
            options={
                "base_url": None,
                "access_key": "access_key",
                "secret_key": "secret_key",
            }
        )
        is False
    )
    assert credentials_are_defined(
        options={
            "base_url": "http://localhost:5000",
            "access_key": "access_key",
            "secret_key": "secret_key",
        }
    )


def test_destination_folder_exists_when_folder_does_not_exist():
    assert (
        destination_folder_exists(options={"destination": "/nonexistent/path"}) is False
    )


def test_destination_folder_exists_when_folder_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert destination_folder_exists(options={"destination": tmpdir}) is True


def test_exit_if_destination_exists_should_not_exit_when_folder_does_not_exist():
    exit_if_destination_exists(options={"destination": "/nonexistent/path"})


def test_exit_if_destination_exists_should_not_exit_when_force_is_true():
    with tempfile.TemporaryDirectory() as tmpdir:
        exit_if_destination_exists(options={"destination": tmpdir, "force": True})


def test_exit_if_destination_exists_should_exit_when_folder_exists_and_no_force():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(SystemExit) as exc_info:
            exit_if_destination_exists(options={"destination": tmpdir, "force": False})
        assert exc_info.value.code == 1


def test_exit_if_destination_exists_should_not_exit_when_folder_with_force():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "RHEL-10")
        exit_if_destination_exists(options={"destination": test_dir, "force": True})


def test_exit_if_variants_are_unknown():
    exit_if_variants_are_unknown(options={"variants": ["AppStream", "BaseOS"]})
    with pytest.raises(SystemExit):
        exit_if_variants_are_unknown(options={"variants": ["Unknown"]})


def test_exit_if_channel_is_unknown():
    exit_if_channel_is_unknown(options={"channel": "nightly"})
    with pytest.raises(SystemExit):
        exit_if_channel_is_unknown(options={"channel": "unknown"})
