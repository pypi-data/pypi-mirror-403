import os
import sys
import stat
import site
import shutil
import logging
import requests
import subprocess
import dotenv
import poly_hammer_utils
from pathlib import Path
from poly_hammer_utils.constants import BLENDER_STARTUP_SCRIPT

REPO_ROOT = Path(__file__).parent.parent.parent.parent
UNREAL_PROJECT  =  Path(os.environ.get('UNREAL_PROJECT', ''))
UNREAL_EXE  =  os.environ.get('UNREAL_EXE')
UNREAL_STARTUP_SCRIPT = Path(__file__).parent / 'resources' / 'scripts' / 'unreal' / 'init_unreal.py'

dotenv.load_dotenv()


def shell(command: str, **kwargs):
    """
    Runs the command is a fully qualified shell.

    Args:
        command (str): A command.

    Raises:
        OSError: The error cause by the shell.
    """
    process = subprocess.Popen(
        command,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs
    )

    output = []
    for line in iter(process.stdout.readline, ""): # type: ignore
        output += [line.rstrip()]
        sys.stdout.write(line)

    process.wait()

    if process.returncode != 0:
        raise OSError("\n".join(output))
    

def download_release_file(
        url: str, 
        save_path: Path, 
        chunk_size: int = 128, 
        auth_token: str | None = None
    ):
    if save_path.exists():
        os.remove(save_path)

    headers = {
        "Accept": "application/octet-stream",
    }
    if auth_token:
        headers["Authorization"] = f"token {auth_token}"

    request = requests.get(url, headers=headers, stream=True)
    os.makedirs(save_path.parent, exist_ok=True)
    with open(save_path, "wb") as fd:
        logging.info(f'Downloading chunk from "{url}"...')
        for chunk in request.iter_content(chunk_size=chunk_size):
            fd.write(chunk)
    

def download_and_unzip_to_folder(
    url: str, 
    save_path: Path, 
    chunk_size: int = 128, 
    auth_token: str | None = None
) -> list[Path]:
    """
    Downloads a zip file from a url and extracts it to the given folder.

    Args:
        url (str): A url to a zip file.
        save_path (Path): The local folder path where the unzipped contents will be.
        chunk_size (int, optional): The chunk size to stream the file download. Defaults to 128.

    Returns:
        list[Path]: A list of the final file paths extracted.
    """
    final_file_paths = []

    zip_file_path = save_path.parent / f"{save_path.name}.zip"

    if save_path.exists():
        shutil.rmtree(save_path)

    if zip_file_path.exists():
        os.remove(zip_file_path)

    headers = {
        "Accept": "application/octet-stream",
    }
    if auth_token:
        headers["Authorization"] = f"token {auth_token}"

    request = requests.get(url, headers=headers, stream=True, allow_redirects=True)
    request.raise_for_status()  # Raise an error for bad status codes
    
    os.makedirs(save_path.parent, exist_ok=True)
    with open(zip_file_path, "wb") as fd:
        logging.info(f'Downloading chunk from "{url}"...')
        for chunk in request.iter_content(chunk_size=chunk_size):
            fd.write(chunk)

    logging.info(f'Un-zipping file "{zip_file_path}"...')
    shutil.unpack_archive(filename=zip_file_path, extract_dir=save_path, format="zip")
    logging.info(f'Removing archive "{zip_file_path}"...')
    os.remove(zip_file_path)

    # make all files in the build path read, write, and executable
    logging.info(f'Modifying file permissions for everything in "{save_path}"...')
    for root, _, files in os.walk(str(save_path)):
        for file_name in files:
            file_path = Path(root) / file_name
            os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            final_file_paths.append(file_path)

    return final_file_paths
        

def get_blender_executable(version: str) -> str:
    if sys.platform == 'win32':
        return rf"C:\Program Files\Blender Foundation\Blender {version}\blender.exe"
    elif sys.platform == 'darwin':
        return '/Applications/Blender.app/Contents/MacOS/Blender'
    elif sys.platform == 'linux':
        return '/snap/bin/blender'
    
    raise OSError('Unsupported platform! Cant get Blender executable path.')

def get_unreal_executable(version: str) -> str:
    if sys.platform == 'win32':
        return rf'C:\Program Files\Epic Games\UE_{version}\Engine\Binaries\Win64\UnrealEditor.exe'
    # elif sys.platform == 'darwin':
    #     return None
    # elif sys.platform == 'linux':
    #     return None
    raise OSError('Unsupported platform! Cant get Unreal executable path.')

def launch_blender(version: str, debug: str):
    exe_path = get_blender_executable(version)

    if exe_path:
        command = f'"{exe_path}" --python-use-system-env --python "{BLENDER_STARTUP_SCRIPT}"'
        shell(
            command, 
            env={
                **os.environ.copy(), 
                'PYTHONUNBUFFERED': '1',
                'BLENDER_APP_VERSION': version,
                'BLENDER_DEBUGGING_ON': debug,
                'PYTHONPATH': os.pathsep.join(
                    site.getsitepackages() + [str(Path(poly_hammer_utils.__file__).parent.parent)]
                )
            }
        )


def launch_unreal(version: str, debug: str):
    exe_path = get_unreal_executable(version)

    if UNREAL_EXE:
        exe_path = UNREAL_EXE

    if not UNREAL_PROJECT.exists():
        raise FileNotFoundError('Unreal project not found! Please set the environment variable "UNREAL_PROJECT" to the project path.')

    if exe_path:
        command = f'"{exe_path}" "{UNREAL_PROJECT}" -stdout -nopause -forcelogflush -verbose'
        shell(
            command, 
            env={
                **os.environ.copy(),
                'UNREAL_APP_VERSION': version,
                'UNREAL_DEBUGGING_ON': debug,
                'UE_PYTHONPATH': os.pathsep.join([
                    *site.getsitepackages(),
                    str(Path(poly_hammer_utils.__file__).parent.parent.absolute()), 
                    str(UNREAL_STARTUP_SCRIPT.parent.absolute())
                ])
            }
        )


if __name__ == "__main__":
    app_name = sys.argv[1]
    app_version = sys.argv[2]
    debug_on = sys.argv[3]

    if app_name == 'blender':
        launch_blender(
            version=app_version,
            debug=debug_on
        )

    if app_name == 'unreal':
        launch_unreal(
            version=app_version,
            debug=debug_on
        )