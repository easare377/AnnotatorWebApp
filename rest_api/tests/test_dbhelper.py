from types import SimpleNamespace

from django.test import TestCase

from rest_api import dbhelper
from rest_api.models import Projects


class ChangeProjectsDetailsTests(TestCase):
    def setUp(self):
        self.project = Projects.objects.create(
            project_name="Original project",
            description="Original description",
        )

    def test_changes_project_name_and_description(self):
        dbhelper.change_projects_details(
            self.project.project_id,
            "Renamed Project-2_test",
            "Updated description",
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.project_name, "Renamed Project-2_test")
        self.assertEqual(self.project.description, "Updated description")

    def test_clears_description_when_new_description_is_none(self):
        dbhelper.change_projects_details(
            self.project.project_id,
            "Renamed Project-2_test",
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.project_name, "Renamed Project-2_test")
        self.assertIsNone(self.project.description)

    def test_trims_surrounding_spaces(self):
        dbhelper.change_projects_details(
            self.project.project_id,
            "   Renamed Project   ",
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.project_name, "Renamed Project")

    def test_rejects_an_empty_project_name(self):
        for invalid_name in ("", "   "):
            with self.subTest(project_name=invalid_name):
                with self.assertRaisesRegex(ValueError, "cannot be empty"):
                    dbhelper.change_projects_details(
                        self.project.project_id,
                        invalid_name,
                        "Updated description",
                    )

    def test_rejects_unsupported_characters(self):
        invalid_names = ("Project@name", "Project.name", "Project/name")

        for invalid_name in invalid_names:
            with self.subTest(project_name=invalid_name):
                with self.assertRaisesRegex(ValueError, "can only contain"):
                    dbhelper.change_projects_details(
                        self.project.project_id,
                        invalid_name,
                        "Updated description",
                    )

    def test_rejects_names_without_letters_or_numbers(self):
        with self.assertRaisesRegex(ValueError, "at least one letter or number"):
            dbhelper.change_projects_details(
                self.project.project_id,
                "-_",
            )

    def test_rejects_a_project_name_that_begins_with_a_number(self):
        with self.assertRaisesRegex(ValueError, "cannot begin with a number"):
            dbhelper.change_projects_details(
                self.project.project_id,
                "2Project",
            )

    def test_accepts_name_and_description_at_maximum_length(self):
        project_name = "A" * 50
        description = "D" * 255

        dbhelper.change_projects_details(
            self.project.project_id,
            project_name,
            description,
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.project_name, project_name)
        self.assertEqual(self.project.description, description)

    def test_rejects_a_project_name_longer_than_50_characters(self):
        with self.assertRaisesRegex(ValueError, "50 characters"):
            dbhelper.change_projects_details(
                self.project.project_id,
                "A" * 51,
            )

    def test_rejects_a_description_longer_than_255_characters(self):
        with self.assertRaisesRegex(ValueError, "255 characters"):
            dbhelper.change_projects_details(
                self.project.project_id,
                "Project name",
                "D" * 256,
            )


class CreateProjectTests(TestCase):
    def setUp(self):
        dbhelper.add_annotation_type_if_not_exist()

    @staticmethod
    def project_info(name, description=None, object_classes=None):
        return SimpleNamespace(
            name=name,
            description=description,
            project_setup=SimpleNamespace(
                annotation_type="POLYGON",
                object_classes=object_classes or [],
            ),
        )

    def test_create_project_uses_normalized_project_name(self):
        project = dbhelper.create_project(
            self.project_info("   New Project-1_test   ")
        )

        self.assertEqual(project.project_name, "New Project-1_test")

    def test_create_project_rejects_unsupported_characters(self):
        with self.assertRaisesRegex(ValueError, "can only contain"):
            dbhelper.create_project(self.project_info("New Project!"))

    def test_create_project_rejects_a_name_that_begins_with_a_number(self):
        with self.assertRaisesRegex(ValueError, "cannot begin with a number"):
            dbhelper.create_project(self.project_info("2New Project"))

    def test_create_project_rejects_a_class_name_that_begins_with_a_number(self):
        object_class = SimpleNamespace(
            class_name="2Vehicle",
            color="#123456",
            description="Vehicle class",
        )

        with self.assertRaisesRegex(ValueError, "Class name must begin with a letter"):
            dbhelper.create_project(
                self.project_info("New Project", object_classes=[object_class])
            )

    def test_create_project_rejects_duplicate_class_names_ignoring_case(self):
        object_classes = [
            SimpleNamespace(
                class_name="Vehicle",
                color="#123456",
                description="First class",
            ),
            SimpleNamespace(
                class_name="vehicle",
                color="#654321",
                description="Duplicate class",
            ),
        ]

        with self.assertRaisesRegex(ValueError, "already exists"):
            dbhelper.create_project(
                self.project_info("New Project", object_classes=object_classes)
            )

    def test_create_project_rejects_more_than_255_classes(self):
        object_classes = [
            SimpleNamespace(
                class_name=f"Class{index}",
                color="#123456",
                description=None,
            )
            for index in range(256)
        ]

        with self.assertRaisesRegex(ValueError, "more than 255 classes"):
            dbhelper.create_project(
                self.project_info("New Project", object_classes=object_classes)
            )

    def test_create_project_enforces_name_and_description_lengths(self):
        invalid_projects = (
            (self.project_info("A" * 51), "50 characters"),
            (self.project_info("New Project", "D" * 256), "255 characters"),
        )

        for project_info, error_message in invalid_projects:
            with self.subTest(error_message=error_message):
                with self.assertRaisesRegex(ValueError, error_message):
                    dbhelper.create_project(project_info)
