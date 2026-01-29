from _typeshed import Incomplete
from pydantic_settings import BaseSettings
from typing import Literal
from uuid import UUID

class S3Settings(BaseSettings):
    model_config: Incomplete
    access_key_id: str
    secret_access_key: str
    region: str
    endpoint: str
    addressing_style: Literal['path', 'virtual']
    bucket: str
    @classmethod
    def validate_endpoint(cls, v: str | None) -> str | None: ...
    @classmethod
    def validate_bucket_name(cls, v: str | None) -> str | None: ...

class CDSSettings(BaseSettings):
    model_config: Incomplete
    release_id: UUID
    s3: S3Settings

class GitLabCISettings(BaseSettings):
    model_config: Incomplete
    project_name: str | None
    project_path: str | None
    project_url: str | None
    commit_sha: str | None
    commit_short_sha: str | None
    commit_ref_name: str | None
    commit_branch: str | None
    pipeline_id: str | None
    pipeline_url: str | None
    job_id: str | None
    job_url: str | None
    runner_description: str | None
    runner_tags: str | None
    environment_name: str | None
    environment_url: str | None

class AppSettings(BaseSettings):
    model_config: Incomplete
    cds: CDSSettings
    gitlab_ci: GitLabCISettings
