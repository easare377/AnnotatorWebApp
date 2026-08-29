"""Tests for the project's development-server defaults."""

from django.core.management import get_commands, load_command_class
from django.test import SimpleTestCase


class RunserverCommandTests(SimpleTestCase):
    def test_runserver_defaults_are_reachable_from_docker(self):
        self.assertEqual(get_commands()["runserver"], "rest_api")

        command = load_command_class("rest_api", "runserver")

        self.assertEqual(command.default_addr, "0.0.0.0")
        self.assertEqual(command.default_port, "8000")
