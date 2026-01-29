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
    model_config: Incomplete
    cds: CDSSettings
    gitlab_ci: GitLabCISettings
