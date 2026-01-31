import os
import sys
import tomlkit
import logging
from pathlib import Path
from poly_hammer_utils.utilities import shell, get_blender_executable

logger = logging.getLogger(__name__)

def get_addon_id(
        source_folder: Path,
    ) -> str:
    file_path = source_folder / 'blender_manifest.toml'
    # Read the id from the manifest file
    if file_path.exists():
        manifest_data = tomlkit.parse(file_path.read_text())
        return manifest_data.get('id', '')
    return ''


def get_addon_version(
        source_folder: Path,
    ) -> str:
    file_path = source_folder / 'blender_manifest.toml'
    # Read the version from the manifest file
    if file_path.exists():
        manifest_data = tomlkit.parse(file_path.read_text())
        return manifest_data.get('version', '')
    return ''

def package_extension(
        source_folder: Path, 
        output_folder: Path,
        blender_version: str = '4.5',
        split_platforms: bool = False,
        docker: bool = False,
    ) -> list[Path]:
    blender_executable = get_blender_executable(version=blender_version)

    addon_version = get_addon_version(source_folder=source_folder)
    addon_id = get_addon_id(source_folder=source_folder)
    logger.info(f'Packaging extension {addon_id} version: {addon_version}')

    if docker:
        # On Linux, set user to avoid permission issues with Docker-created files
        user_flag = ''
        if sys.platform != 'win32':
            user_flag = f'--user {os.getuid()}:{os.getgid()} '
        
        command = (
            f'docker run '
            f'{user_flag}'
            f'-v {source_folder.as_posix()}:/src '
            f'-v {output_folder.as_posix()}:/output '
            f'ghcr.io/poly-hammer/blender-linux:{blender_version} '
            f'blender --command extension build --source-dir /src --output-dir /output'
        )
    else:
        # wrap in quotes for Windows paths with spaces
        if sys.platform == 'win32':
            blender_executable = f'"{blender_executable}"'

        command = f'{blender_executable} --command extension build --source-dir {source_folder.as_posix()} --output-dir {output_folder.as_posix()}'
    
    if split_platforms:
        command += ' --split-platforms'
        
    shell(command, cwd=source_folder)

    return list(output_folder.glob(f'{addon_id}-{addon_version}-*.zip'))