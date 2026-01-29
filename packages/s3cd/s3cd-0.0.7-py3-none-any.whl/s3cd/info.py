from datetime import UTC, datetime
from typing import Any

from s3cd.settings import AppSettings


class ReleaseInfoGenerator:
    def __init__(self):
        self.config = AppSettings()  # pyright: ignore[reportCallIssue]  # type: ignore[call-arg]

    def generate(self) -> dict[str, Any]:
        now = datetime.now(UTC)

        info: dict[str, Any] = {
            'CDS_DATETIME': now.isoformat(),
            'CDS_TIMESTAMP': now.timestamp(),
            'CDS_RELEASE_ID': str(self.config.cds.release_id),
            'CDS_S3_BUCKET': self.config.cds.s3.bucket,
            'CDS_S3_ENDPOINT': self.config.cds.s3.endpoint,
            'CDS_S3_REGION': self.config.cds.s3.region,
            'CDS_S3_ADDRESSING_STYLE': self.config.cds.s3.addressing_style,
            'CI_PROJECT_NAME': self.config.gitlab.project_name,
            'CI_PROJECT_PATH': self.config.gitlab.project_path,
            'CI_PROJECT_URL': self.config.gitlab.project_url,
            'CI_COMMIT_SHA': self.config.gitlab.commit_sha,
            'CI_COMMIT_SHORT_SHA': self.config.gitlab.commit_short_sha,
            'CI_COMMIT_REF_NAME': self.config.gitlab.commit_ref_name,
            'CI_COMMIT_BRANCH': self.config.gitlab.commit_branch,
            'CI_PIPELINE_ID': self.config.gitlab.pipeline_id,
            'CI_PIPELINE_URL': self.config.gitlab.pipeline_url,
            'CI_JOB_ID': self.config.gitlab.job_id,
            'CI_JOB_URL': self.config.gitlab.job_url,
            'CI_RUNNER_DESCRIPTION': self.config.gitlab.runner_description,
            'CI_RUNNER_TAGS': self.config.gitlab.runner_tags,
            'CI_ENVIRONMENT_NAME': self.config.gitlab.environment_name,
            'CI_ENVIRONMENT_URL': self.config.gitlab.environment_url,
        }

        return info
