"""Run Django on an address reachable from local Docker containers."""

from django.contrib.staticfiles.management.commands.runserver import (
    Command as StaticFilesRunserverCommand,
)


class Command(StaticFilesRunserverCommand):
    """Default the development server to all interfaces on port 8000."""

    default_addr = "0.0.0.0"
    default_port = "8000"
