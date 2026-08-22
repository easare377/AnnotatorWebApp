from storages.backends.s3boto3 import S3Boto3Storage
import io


class UFECLAnnotatorBucket(S3Boto3Storage):
    bucket_name = 'uf-ecl-annotator-bucket'

    def save(self, name, content, max_length=None):
        blob_name = super().save(name, content, max_length)
        return self.url(blob_name)

    def save_to_exported_masks_folder(self, blob_url, blob):
        return self.save(f'exported-masks/{blob_url}', blob)

    def save_to_exported_voc_folder(self, blob_name, blob):
        return self.save(f'exported-vocs/{blob_name}', blob)

    def save_to_exported_json_folder(self, blob_name, json):
        # Convert the JSON string to a BytesIO object (a file-like object in memory)
        json_bytes = io.BytesIO(json.encode('utf-8'))
        return self.save(f'exported-jsons/{blob_name}', json_bytes)

    def save_to_exported_rgb_masks_folder(self, blob_name, blob):
        return self.save(f'rgb-exported-masks/{blob_name}', blob)

    def save_to_png_folder(self, blob_name, blob):
        return self.save(f'uploads/png/{blob_name}', blob)

    def save_to_jpg_folder(self, blob_name, blob):
        return self.save(f'uploads/jpg/{blob_name}', blob)

    def save_to_zip_folder(self, blob_name, blob):
        return self.save(f'exports/{blob_name}', blob)
