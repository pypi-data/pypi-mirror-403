# s3cd

S3 Content Delivery tool - CLI for uploading and copying static files/artifacts to S3

[![PyPI](https://img.shields.io/pypi/v/s3cd)](https://pypi.org/project/s3cd/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/s3cd)](https://pypi.org/project/s3cd/)

[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=rocshers_s3cd&metric=coverage)](https://sonarcloud.io/summary/new_code?id=rocshers_s3cd)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=rocshers_s3cd&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=rocshers_s3cd)

[![Downloads](https://static.pepy.tech/badge/s3cd)](https://pepy.tech/project/s3cd)
[![GitLab stars](https://img.shields.io/gitlab/stars/rocshers/python/s3cd)](https://gitlab.com/rocshers/python/s3cd)
[![GitLab last commit](https://img.shields.io/gitlab/last-commit/rocshers/python/s3cd)](https://gitlab.com/rocshers/python/s3cd)

## Features

- 📦 **Upload** directories recursively to S3 buckets maintaining structure
- 🔄 **Copy** objects between S3 buckets without local download (server-side copy)
- 🚀 **Multipart upload** support for large files
- 📝 Automatic **__info.json** generation with GitLab CI/CD metadata
- 🔐 Flexible **authentication** via environment variables or CLI flags
- 🌐 Support for **S3-compatible** storage (MinIO, Yandex Object Storage, etc.)
- 🎯 **Path-style** and **virtual-hosted-style** S3 addressing

## Quick Start

```bash
export CDS_RELEASE_ID=$(uuidgen --time-v7)

export CDS_S3_ACCESS_KEY_ID="your-access-key"
export CDS_S3_SECRET_ACCESS_KEY="your-secret-key"
export CDS_S3_BUCKET="content-delivery-storage"

uvx s3cd upload ./dist
```

## Environment

```bash
# Meta
export CDS_RELEASE_ID=$(uuidgen --time-v7)
# S3
export CDS_S3_ACCESS_KEY_ID="your-access-key"
export CDS_S3_SECRET_ACCESS_KEY="your-secret-key"
export CDS_S3_REGION="us-east-1"
export CDS_S3_ENDPOINT="https://s3.amazonaws.com"
export CDS_S3_ADDRESSING_STYLE="virtual"  # or "path"
```

### Contributing

Issue Tracker: <https://gitlab.com/rocshers/python/s3cd/-/issues>  
Source Code: <https://gitlab.com/rocshers/python/s3cd>
