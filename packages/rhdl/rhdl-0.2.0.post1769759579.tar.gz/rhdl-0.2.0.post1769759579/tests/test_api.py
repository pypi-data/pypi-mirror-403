from unittest.mock import Mock, patch
from rhdlcli.api import get_component
from rhdlcli.cli import parse_arguments
from rhdlcli.options import build_options


def test_nrt_get_component_should_filter_by_tag():
    arguments = parse_arguments(
        ["download", "RHEL-9.4", "--channel", "nightly", "--tag", "5.14.0-570"]
    )
    env_variables = {
        "RHDL_API_URL": "https://api.example.com",
        "RHDL_ACCESS_KEY": "test_key",
        "RHDL_SECRET_KEY": "test_secret",
    }
    options = build_options(arguments, env_variables)

    mock_response = Mock()
    mock_response.json.return_value = {
        "components": [
            {
                "compose_id": "RHEL-9.4.0-20240101.n.0",
                "tags": ["nightly", "5.14.0-570"],
            }
        ]
    }
    mock_response.raise_for_status = Mock()

    with patch("rhdlcli.api.HmacSession") as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = mock_response

        result = get_component(options)

        mock_session_class.assert_called_once_with(
            base_url="https://api.example.com",
            access_key="test_key",
            secret_key="test_secret",
        )

        assert options["tags"] == ["5.14.0-570"]
        assert options["channel"] == "nightly"

        mock_session.get.assert_called_once_with(
            "/api/v1/components",
            params={
                "compose_id_startswith": "RHEL-9.4",
                "state": "active",
                "sort": "-released_at",
                "tag": ["nightly", "5.14.0-570"],
            },
        )

        assert result == mock_response.json()["components"][0]
