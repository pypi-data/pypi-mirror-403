import os
import sys
import logging
import boto3
import httpx
from pathlib import Path
from poly_hammer_utils.constants import ENVIRONMENT
from poly_hammer_utils.utilities import shell, get_blender_executable

logger = logging.getLogger(__name__)

ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
REGION = os.environ.get('AWS_REGION')

BASE_URL = 'https://api.portal.staging.polyhammer.com'
if ENVIRONMENT == 'production':
    BASE_URL = 'https://api.portal.polyhammer.com'

PORTAL_API_KEY = os.environ.get('PORTAL_API_KEY')

def sync_extensions_from_s3(
        repo_folder: Path,
        bucket: str,
        s3_prefix: str = ''
    ) -> list[Path]:
    """
    Downloads all .zip extension files from an S3 folder to a local directory.

    Args:
        repo_folder (Path): Local directory to download files to.
        bucket (str): The S3 bucket name.
        s3_prefix (str, optional): Prefix (folder path) in S3. Defaults to ''.

    Returns:
        list[Path]: List of local file paths that were downloaded.
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION,
    )

    repo_folder.mkdir(parents=True, exist_ok=True)

    # List all objects in the S3 prefix
    prefix = f'{s3_prefix}/' if s3_prefix and not s3_prefix.endswith('/') else s3_prefix
    logger.info(f'Listing objects in s3://{bucket}/{prefix}')

    downloaded_files = []
    paginator = s3_client.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            filename = key.split('/')[-1]

            # Only download .zip files
            if not filename.endswith('.zip'):
                continue

            local_path = repo_folder / filename
            logger.info(f'Downloading s3://{bucket}/{key} to "{local_path}"')
            s3_client.download_file(bucket, key, str(local_path))
            downloaded_files.append(local_path)

    logger.info(f'Successfully downloaded {len(downloaded_files)} file(s) from S3')
    return downloaded_files


def upload_extensions_to_s3(
        repo_folder: Path,
        bucket: str,
        s3_prefix: str = ''
    ) -> list[str]:
    """
    Uploads extension .zip files and the index.json to S3.
    Only uploads .zip files if they are newer than the S3 version.
    Always uploads the index.json file.

    Args:
        repo_folder (Path): Local directory containing files to upload.
        bucket (str): The S3 bucket name.
        s3_prefix (str, optional): Prefix (folder path) in S3. Defaults to ''.

    Returns:
        list[str]: List of S3 keys that were uploaded.
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION,
    )

    # Build a map of S3 object keys to their last modified times
    prefix = f'{s3_prefix}/' if s3_prefix and not s3_prefix.endswith('/') else s3_prefix
    s3_objects = {}
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            s3_objects[obj['Key']] = obj['LastModified']

    uploaded_keys = []
    # Collect .json and .zip files
    file_paths = list(repo_folder.glob('*.json')) + list(repo_folder.glob('*.zip'))

    for file_path in file_paths:
        if not file_path.exists():
            logger.warning(f'File "{file_path}" does not exist, skipping')
            continue

        # Build the S3 key
        s3_key = f'{s3_prefix}/{file_path.name}' if s3_prefix else file_path.name
        s3_key = s3_key.lstrip('/')

        # For .zip files, check if local file is newer than S3 version
        if file_path.suffix == '.zip' and s3_key in s3_objects:
            import datetime
            local_mtime = datetime.datetime.fromtimestamp(
                file_path.stat().st_mtime, 
                tz=datetime.timezone.utc
            )
            s3_mtime = s3_objects[s3_key]
            if local_mtime <= s3_mtime:
                logger.info(f'Skipping "{file_path.name}" (not newer than S3 version)')
                continue

        # Determine content type
        if file_path.suffix == '.zip':
            content_type = 'application/zip'
        elif file_path.suffix == '.json':
            content_type = 'application/json'
        else:
            content_type = 'application/octet-stream'

        logger.info(f'Uploading "{file_path}" to s3://{bucket}/{s3_key}')
        s3_client.upload_file(
            Filename=str(file_path),
            Bucket=bucket,
            Key=s3_key,
            ExtraArgs={'ContentType': content_type}
        )
        uploaded_keys.append(s3_key)

    logger.info(f'Successfully uploaded {len(uploaded_keys)} file(s) to S3')
    return uploaded_keys


def generate_extension_index(
        repo_folder: Path, 
        blender_version: str = '4.5',
        docker: bool = False,
    ):
    blender_executable = get_blender_executable(version=blender_version)

    if docker:
        command = (
            f'docker run '
            f'-v {repo_folder.as_posix()}:/repo '
            f'ghcr.io/poly-hammer/blender-linux:{blender_version} '
            f'blender --command extension server-generate --repo-dir /repo'
        )
    else:
        # wrap in quotes for Windows paths with spaces
        if sys.platform == 'win32':
            blender_executable = f'"{blender_executable}"'

        command = f'{blender_executable} --command extension server-generate --repo-dir {repo_folder.as_posix()}'

    shell(command)

def trigger_poly_hammer_portal_extension_index_refresh() -> httpx.Response:
    """Trigger sync of all extensions from S3."""
    logger.info("Triggering extension sync...")
    
    url = f"{BASE_URL}/api/v1/admin/extensions/sync"
    headers = {"X-Admin-API-Key": PORTAL_API_KEY}

    response = httpx.post(url, headers=headers, timeout=60.0)

    if response.status_code == 200:
        data = response.json()
        logger.info("Sync complete!")
        logger.info(f"Extensions processed: {data['extensions_processed']}")
        logger.info(f"Platforms synced: {data['total_platforms_synced']}")
        
        if data.get("errors"):
            logger.error(f"Errors: {data['errors']}")
        
        if data.get("details"):
            logger.info("Extension details:")
            for ext in data["details"]:
                logger.info(f"- {ext['extension_id']}: {ext['versions_synced']} versions, {ext['platforms_synced']} platforms")
    else:
        logger.error(f"Failed with status {response.status_code}")
        logger.error(f"Response: {response.text}")

    return response

def update_extension_index(
        repo_folder: Path, 
        bucket: str,
        s3_folder: str,
        blender_version: str = '4.5',
        docker: bool = False,
    ):
    """
    Syncs extensions from S3, regenerates the index locally, and uploads
    any new or modified files back to S3.

    Args:
        repo_folder (Path): Local directory for the extension repository.
        bucket (str): The S3 bucket name.
        s3_folder (str): The folder path in S3.
        blender_version (str, optional): Blender version to use. Defaults to '4.5'.
        docker (bool, optional): Whether to use Docker for index generation. Defaults to False.
    """
    # Step 1: Generate the extension index from all local .zip files
    generate_extension_index(
        repo_folder=repo_folder,
        blender_version=blender_version,
        docker=docker,
    )

    # Step 2: Upload new/modified .zip files and the updated index.json back to S3
    upload_extensions_to_s3(
        repo_folder=repo_folder,
        bucket=bucket,
        s3_prefix=s3_folder,
    )

    # Step 3: Trigger the Poly Hammer Portal to refresh its extension index
    trigger_poly_hammer_portal_extension_index_refresh()