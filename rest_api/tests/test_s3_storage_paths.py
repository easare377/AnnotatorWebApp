"""Tests for provider-neutral paths used by the S3 storage helper."""

from unittest.mock import patch

from django.test import SimpleTestCase

from rest_api.s3_storage.uf_ecl_annotator_bucket import UFECLAnnotatorBucket


class S3StoragePathTests(SimpleTestCase):
    @patch.object(UFECLAnnotatorBucket, "save", return_value="https://example.com")
    def test_helpers_write_below_the_userdata_prefix(self, save):
        storage = UFECLAnnotatorBucket()
        blob = object()

        storage.save_to_exported_masks_folder("mask.png", blob)
        storage.save_to_exported_rgb_masks_folder("rgb.png", blob)
        storage.save_to_exported_voc_folder("labels.xml", blob)
        storage.save_to_exported_json_folder("labels.json", "{}")
        storage.save_to_png_folder("image.png", blob)
        storage.save_to_jpg_folder("image.jpg", blob)
        storage.save_to_zip_folder("project.zip", blob)

        self.assertEqual(
            [call.args[0] for call in save.call_args_list],
            [
                "userdata/exports/exported-segmentation/mask/mask.png",
                "userdata/exports/exported-segmentation/rgb/rgb.png",
                "userdata/exports/exported-vocs/labels.xml",
                "userdata/exports/exported-jsons/labels.json",
                "userdata/uploads/png/image.png",
                "userdata/uploads/jpg/image.jpg",
                "userdata/exports/exported-segmentation/zip/project.zip",
            ],
        )
