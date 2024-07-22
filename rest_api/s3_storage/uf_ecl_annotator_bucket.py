from storages.backends.s3boto3 import S3Boto3Storage


class UFECLAnnotatorBucket(S3Boto3Storage):
    bucket_name = 'uf-ecl-annotator-bucket'
