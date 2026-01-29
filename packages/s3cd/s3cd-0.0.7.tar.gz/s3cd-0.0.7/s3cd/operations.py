import json
from pathlib import Path

import typer

from s3cd.info import ReleaseInfoGenerator
from s3cd.s3 import S3Client, S3ClientError
from s3cd.settings import AppSettings


class S3Operations:
    def __init__(self, verbose: bool = False):
        self.config = AppSettings()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
        self.s3_client = S3Client(self.config.cds.s3)

        self.verbose = verbose

    def _log(self, message: str, only_verbose: bool = False, err: bool = False) -> None:
        if not only_verbose:
            typer.echo(message, err=err)
            return

        if only_verbose and self.verbose:
            typer.echo(message, err=err)

    def validate_index_html(self, release_path: Path) -> None:
        index_html_path = release_path / 'index.html'

        if not index_html_path.exists():
            self._log(f'Error: File not found: {index_html_path}', err=True)
            raise typer.Exit(1)

    def upload(self, source_dir: str) -> None:
        source_path = Path(source_dir)
        source_release_path = source_path / str(self.config.cds.release_id)

        self.validate_index_html(source_release_path)

        self._upload_files(source_path)
        self._upload_info_json()

    def _upload_files(self, source_path: Path) -> None:
        self._log(f'Uploading {source_path} to s3://{self.config.cds.s3.bucket}/')

        uploaded_count = 0
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(source_path)
                s3_key = relative_path.as_posix()

                self._log(f'Uploading: {file_path} -> s3://{self.config.cds.s3.bucket}/{s3_key}', only_verbose=True)

                try:
                    self.s3_client.upload_file(str(file_path), self.config.cds.s3.bucket, s3_key)
                    uploaded_count += 1

                except S3ClientError as e:
                    self._log(f'Error: {e}', err=True)
                    raise typer.Exit(1) from e

        self._log(f'Uploaded {uploaded_count} files successfully')

    def _upload_info_json(self) -> None:
        release_info_json = ReleaseInfoGenerator().generate()

        info_key = f'{self.config.cds.release_id}/.cds/release.json'
        self._log(f'Uploading release.json to s3://{self.config.cds.s3.bucket}/{info_key}')

        try:
            self.s3_client.put_object(
                self.config.cds.s3.bucket,
                info_key,
                json.dumps(release_info_json, indent=2, ensure_ascii=False).encode('utf-8'),
            )
            self._log(f'Generated release.json at s3://{self.config.cds.s3.bucket}/{info_key}', only_verbose=True)

        except S3ClientError as e:
            self._log(f'Error: {e}', err=True)
            raise typer.Exit(1) from e
