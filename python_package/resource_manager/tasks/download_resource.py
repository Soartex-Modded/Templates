import subprocess
import tempfile
import zipfile

import requests
import os


def download_resource(resource):
    """
    Downloads and unpacks assets for a resource from either git or curseforge.
    :param resource: dict containing download_dir, and either download_repo or curseforge project and file ids
    """
    download_dir = os.path.expanduser(resource['download_dir'])

    if os.path.exists(download_dir):
        print("Resource already downloaded.")
        return

    # DOWNLOAD FROM GIT
    if "download_repo" in resource:
        os.makedirs(download_dir, exist_ok=True)
        subprocess.Popen(f"git clone {resource['download_repo']} .", cwd=download_dir)

    # DOWNLOAD FROM CURSEFORGE
    if "download_project_id" in resource:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
        }
        download_url = requests.get(
            f"https://addons-ecs.forgesvc.net/api/v2/addon/{resource['download_project_id']}/file/{resource['download_file_id']}/download-url",
            headers=headers).text

        with tempfile.TemporaryDirectory() as temp_download_dir:

            temp_download_path = os.path.join(temp_download_dir, "temp.zip")
            with open(temp_download_path, 'wb') as resource_file:
                resource_file.write(requests.get(download_url, headers=headers).content)

            os.makedirs(download_dir, exist_ok=True)
            with zipfile.ZipFile(temp_download_path, 'r') as zip_file:
                [zip_file.extract(file, download_dir) for file in zip_file.namelist()]

