import os
import logging
import zipfile
import tempfile
from pathlib import Path
from poly_hammer_utils.constants import ENVIRONMENT
from poly_hammer_utils.utilities import download_and_unzip_to_folder, download_release_file
from poly_hammer_utils.github.release import GitHubRelease
from poly_hammer_utils.extension.packager import package_extension, get_addon_version
from poly_hammer_utils.extension.server import update_extension_index, sync_extensions_from_s3

BLENDER_EXTENSION_SERVER_S3_BUCKET = 'poly-hammer-portal-staging-app-data'
if ENVIRONMENT == 'production':
    BLENDER_EXTENSION_SERVER_S3_BUCKET = 'poly-hammer-portal-production-app-data'

BLENDER_EXTENSION_SERVER_S3_FOLDER = 'products/blender-extensions/meta_human_dna'

logger = logging.getLogger(__name__)

PREFIX = 'meta_human_dna_core.'

def parse_python_extension_info(prefix: str, url: str) -> tuple[str, str]:
    # parse the platform and arch from the attachment name
    try:
        base = Path(url).name.replace(prefix, '').split('.')[0]
        platform, arch = base.split('-')[-1].split('_')
        python_version = f"py{base.split('-')[0].strip('cp')}"
    except ValueError:
        chunks = Path(url).name.replace(prefix, '').split('.')[0].split('-')
        platform, arch, python_version = chunks[3], chunks[2], f"py{chunks[1]}"

    if platform == 'win':
        platform = 'windows'
    elif platform == 'darwin':
        platform = 'macos'

    if arch in ['x86_64', 'amd64']:
        arch = 'x64'

    return platform, arch, python_version

def parse_blender_extension_zip_info(url: str) -> tuple[str, str]:
    # parse the platform and arch from the attachment name
    base = Path(url).stem.split('-')[-1]
    platform, arch = base.split('_')
    return platform, arch

def parse_file_path_info(file_path: Path) -> tuple[str, str, str]:
    chunks = file_path.parts[-2].split('-')
    platform, arch, python_version = chunks[-3], chunks[-2], chunks[-1].replace('.', '')

    if arch in ['x86_64', 'amd64']:
        arch = 'x64'
    
    if platform == 'mac':
        platform = 'macos'

    return platform, arch, python_version

def get_bindings_folder(root_folder: Path, url: str) -> Path:
    platform, arch, python_version = parse_python_extension_info(prefix=PREFIX, url=url)

    save_path = root_folder / 'bindings' / platform / arch / python_version / Path(url).name
    # Mac python extensions should not have the arch in the name
    if platform == 'macos':
        save_path = root_folder / 'bindings' / platform / arch / python_version / Path(url).name.replace(f'-{arch}', '')

    return save_path

def get_rig_logic_lib(
        auth_token: str
) -> list[Path]:
    file_paths = []
    rig_logic_releases = GitHubRelease(
        repo='poly-hammer/RigLogicLib',
        github_token=auth_token
    )
    tag_name, attachments = rig_logic_releases.get_releases_attachments(tag='latest')
    for asset in attachments:
        name = Path(asset.browser_download_url).stem
        logger.info(f'Downloading RigLogicLib asset: {asset.browser_download_url}')
        file_paths.extend(download_and_unzip_to_folder(
            url=asset.url, 
            save_path=Path(tempfile.mkdtemp()) / name,
            auth_token=auth_token
        ))
    return file_paths

def get_meta_human_dna_core(addon_version: str, auth_token: str) -> list[Path]:
    file_paths = []
    core_releases = GitHubRelease(
        repo='poly-hammer/meta-human-dna-core',
        github_token=auth_token
    )

    # first check if the release already exists
    tag_name, attachments = core_releases.get_releases_attachments(tag=addon_version)

    # trigger the build workflow if the release does not exist
    if tag_name != addon_version or not attachments:
        core_releases.trigger_build_workflow(
            repo='poly-hammer/meta-human-dna-core',
            await_completion=True,
            poll_interval=10,
            timeout=1800
        )
    # now get the release assets
    tag_name, attachments = core_releases.get_releases_attachments(tag=addon_version)
    if tag_name != addon_version or not attachments:
        raise RuntimeError(f'Failed to build meta-human-dna-core release {addon_version}')
    
    root_folder = Path(tempfile.mkdtemp())
    for asset in attachments:
        # Use asset.url (API endpoint) for private repos, not browser_download_url
        save_path = get_bindings_folder(root_folder=root_folder, url=asset.browser_download_url)
        download_release_file(
            auth_token=auth_token, 
            url=asset.url, 
            save_path=save_path
        )
        file_paths.append(save_path)
    return file_paths

def create_release(addon_folder: Path, releases_folder: Path):
    token = os.environ['GH_PAT']

    addon_version = get_addon_version(source_folder=addon_folder)

    # First, sync existing extensions from S3
    sync_extensions_from_s3(
        repo_folder=releases_folder,
        bucket=BLENDER_EXTENSION_SERVER_S3_BUCKET,
        s3_prefix=BLENDER_EXTENSION_SERVER_S3_FOLDER,
    )

    # Create the new .zip files for the addon's various platforms
    addon_zip_files = package_extension(
        source_folder=addon_folder,
        output_folder=releases_folder,
        blender_version=os.environ['BLENDER_VERSION'],
        split_platforms=True,
        docker=True
    )

    # Download the latest RigLogicLib release and extract it
    rig_logic_files = get_rig_logic_lib(auth_token=token)

    # Download the matching meta-human-dna-core release and extract it
    core_files = get_meta_human_dna_core(
        addon_version=addon_version,
        auth_token=token
    )

    # Update each addon .zip to include the rig logic and core bindings
    for addon_zip_file in addon_zip_files:
        platform, arch = parse_blender_extension_zip_info(url=addon_zip_file)
        files_to_zip = rig_logic_files + core_files
        with zipfile.ZipFile(addon_zip_file, mode="a", compression=zipfile.ZIP_DEFLATED) as zip_file_handle:
            for file_path in files_to_zip:
                if file_path in rig_logic_files:
                    _platform, _arch, _python_version = parse_file_path_info(file_path=file_path)
                else:
                    _platform, _arch, _python_version = file_path.parts[-4], file_path.parts[-3], file_path.parts[-2]
                
                # only add files that match the current platform and arch of the addon zip
                if _platform != platform or _arch != arch:
                    continue

                if os.path.exists(file_path):
                    zip_file_handle.write(file_path, arcname=Path('bindings', platform, arch, _python_version, file_path.name).as_posix())
                    logger.info(f"Added {file_path}")
                else:
                    logger.error(f"Error: {file_path} not found")

    # Generate the updated extension index and upload it and the addons .zip file to S3
    update_extension_index(
        repo_folder=releases_folder,
        bucket=BLENDER_EXTENSION_SERVER_S3_BUCKET,
        s3_folder=BLENDER_EXTENSION_SERVER_S3_FOLDER,
        blender_version=os.environ['BLENDER_VERSION'],
        docker=True
    )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    addons_folder = os.environ.get('ADDONS_FOLDER', Path(os.getcwd()) / 'src' / 'addons')
    addons_folder = Path(addons_folder)

    releases_folder = os.environ.get('RELEASES_FOLDER', Path(tempfile.mkdtemp()))
    releases_folder = Path(releases_folder)

    for addon_name in os.listdir(addons_folder):
        addon_folder = addons_folder / addon_name
        create_release(
            addon_folder=addon_folder,
            releases_folder=releases_folder
        )

    # Clean up the releases folder
    for item in releases_folder.iterdir():
        if item.is_file():
            item.unlink()
    releases_folder.rmdir()