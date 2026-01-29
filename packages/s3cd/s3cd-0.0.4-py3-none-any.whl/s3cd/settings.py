from typing import Literal
from uuid import UUID

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='CDS_S3_',
        extra='ignore',
    )

    access_key_id: str
    secret_access_key: str
    region: str
    endpoint: str
    addressing_style: Literal['path', 'virtual'] = 'virtual'
    bucket: str

    @field_validator('endpoint')
    @classmethod
    def validate_endpoint(cls, v: str | None) -> str | None:
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Endpoint must start with http:// or https://')
        return v

    @field_validator('bucket')
    @classmethod
    def validate_bucket_name(cls, v: str | None) -> str | None:
        if v and ('/' in v or '\\' in v):
            raise ValueError('Bucket name must not contain slashes')
        return v


class CDSSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='CDS_',
        extra='ignore',
    )

    release_id: UUID

    s3: S3Settings = S3Settings()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]


class GitLabCISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='CI_',
        extra='ignore',
    )

    project_name: str | None = None
    project_path: str | None = None
    project_url: str | None = None
    commit_sha: str | None = None
    commit_short_sha: str | None = None
    commit_ref_name: str | None = None
    commit_branch: str | None = None
    pipeline_id: str | None = None
    pipeline_url: str | None = None
    job_id: str | None = None
    job_url: str | None = None
    runner_description: str | None = None
    runner_tags: str | None = None
    environment_name: str | None = None
    environment_url: str | None = None


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
    )

    cds: CDSSettings = CDSSettings()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
    gitlab_ci: GitLabCISettings = GitLabCISettings()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
