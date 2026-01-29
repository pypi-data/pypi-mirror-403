import typer

import s3cd
from s3cd.operations import S3Operations

cli = typer.Typer(help='s3cd - S3 Content Delivery tool for uploading and copying files to S3')


def version_callback(value: bool):
    if value:
        print(f'Version of s3cd is {s3cd.__version__}')
        raise typer.Exit(0)


@cli.callback(invoke_without_command=True)
def callback(
    version: bool = typer.Option(
        False,
        '--version',
        callback=version_callback,
        help='Print version of s3cd.',
        is_eager=True,
    ),
):
    pass


@cli.command('upload')
def upload_command(
    source_dir: str = typer.Argument(..., help='Local source directory to upload'),
    verbose: bool = typer.Option(False, '--verbose', '-v', help='Enable verbose output'),
):
    operations = S3Operations(verbose=verbose)
    operations.upload(source_dir)
