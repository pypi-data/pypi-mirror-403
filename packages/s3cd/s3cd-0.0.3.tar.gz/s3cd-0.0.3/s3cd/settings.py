from typing import Literal
from uuid import UUID

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='CDS_S3_', env_file='.env', extra='ignore')

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
    model_config = SettingsConfigDict(env_prefix='CDS_', env_file='.env', extra='ignore')

    release_id: UUID

    s3: S3Settings


class GitLabCISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='CI_', env_file='.env', extra='ignore')

    project_name: str
    project_path: str
    project_url: str
    commit_sha: str
    commit_short_sha: str
    commit_ref_name: str
    commit_branch: str
    pipeline_id: str
    pipeline_url: str
    job_id: str
    job_url: str
    runner_description: str
    runner_tags: str
    environment_name: str
    environment_url: str


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    cds: CDSSettings
    gitlab_ci: GitLabCISettings
