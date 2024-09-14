from storages.backends.s3boto3 import S3Boto3Storage


class UFECLAnnotatorBucket(S3Boto3Storage):
    bucket_name = 'uf-ecl-annotator-bucket'

    def save(self, name, content, max_length=None):
        blob_name = super().save(name, content, max_length)
        return self.url(blob_name)

    def save_to_exported_masks_folder(self, blob_name, blob):
        blob_name = self.save(f'exported-masks/{blob_name}', blob)
        return self.url(blob_name)

    def save_to_exported_rgb_masks_folder(self, blob_name, blob):
        blob_name = self.save(f'rgb-exported-masks/{blob_name}', blob)
        return self.url(blob_name)

    def save_to_png_folder(self, blob_name, blob):
        blob_name = self.save(f'uploads/png/{blob_name}', blob)
        return self.url(blob_name)

    def save_to_jpg_folder(self, blob_name, blob):
        blob_name = self.save(f'uploads/jpg/{blob_name}', blob)
        return self.url(blob_name)

    def save_to_zip_folder(self, blob_name, blob):
        blob_name = self.save(f'exports/{blob_name}', blob)
        return self.url(blob_name)
