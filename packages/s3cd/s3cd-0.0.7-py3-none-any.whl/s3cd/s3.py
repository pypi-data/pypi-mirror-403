import mimetypes
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from s3cd.settings import S3Settings


class S3ClientError(Exception):
    pass


class S3Client:
    def __init__(self, settings: S3Settings):
        self.settings = settings
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = self._create_client()

        return self._client

    def get_content_type(self, file_path: str) -> str:
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            return 'application/octet-stream'
        return content_type

    def _create_client(self) -> None:
        config = Config(s3={'addressing_style': self.settings.addressing_style})

        client_kwargs: dict[str, Any] = {
            'service_name': 's3',
            'aws_access_key_id': self.settings.access_key_id,
            'aws_secret_access_key': self.settings.secret_access_key,
            'region_name': self.settings.region,
            'config': config,
        }

        if self.settings.endpoint:
            client_kwargs['endpoint_url'] = self.settings.endpoint

        return boto3.client(**client_kwargs)

    def upload_file(self, file_path: str, bucket: str, key: str) -> None:
        extra_args = {
            'ContentType': self.get_content_type(file_path),
        }

        try:
            self.client.upload_file(file_path, bucket, key, ExtraArgs=extra_args)

        except ClientError as e:
            raise S3ClientError(f'Failed to upload file {file_path} to s3://{bucket}/{key}: {e}') from e

    def put_object(self, bucket: str, key: str, body: bytes, content_type: str = 'application/json') -> None:
        try:
            self.client.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)

        except ClientError as e:
            raise S3ClientError(f'Failed to put object to s3://{bucket}/{key}: {e}') from e
