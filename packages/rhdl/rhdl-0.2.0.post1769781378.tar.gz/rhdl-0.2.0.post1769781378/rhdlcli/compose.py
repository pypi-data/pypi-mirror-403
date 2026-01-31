from rhdlcli.api import get_compose_versions
from rhdlcli.printer import print_output


def list_compose_versions(options):
    compose_versions = get_compose_versions(options)
    print_output(
        data=compose_versions,
        headers={"name": "RHEL version"},
        options=options,
    )
