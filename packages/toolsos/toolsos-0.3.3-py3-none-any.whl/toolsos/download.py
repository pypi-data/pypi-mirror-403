import pathlib
import shutil
import zipfile

import requests


def download(url: str, dest_path: pathlib.Path):
    r = requests.get(url, stream=True)
    if not r.ok:
        raise ValueError("Download failed: check repo and language")

    with open(dest_path, "wb") as f:
        for chunk in r.iter_content():
            if chunk:
                f.write(chunk)


def unzip(zip_store: pathlib.Path, dest_folder: pathlib.Path):
    with zipfile.ZipFile(zip_store) as zipfile_:
        for filename in zipfile_.namelist():
            zipfile_.extract(filename, path=dest_folder)


class FileLocation:
    GIT_PROVIDER = "https://gitlab.com/os-amsterdam"

    def __init__(
        self,
        dest_folder: str,
        dest_folder_name: str,
        repo: str,
        branch: str,
        subfolder: str,
    ):
        self.dest_folder = pathlib.Path(dest_folder)
        self.dest_folder_name = dest_folder_name
        self.repo = repo
        self.branch = branch
        self.subfolder = subfolder

    @property
    def url(self):
        return f"{self.GIT_PROVIDER}/{self.repo}/-/archive/main/{self.repo}-{self.branch}.zip"

    @property
    def zipfile(self):
        return self.dest_folder / "_temp.zip"

    @property
    def move_folder(self):
        return self.dest_folder / f"{self.repo}-{self.branch}" / self.subfolder

    @property
    def unzipped_folder(self):
        return self.dest_folder / f"{self.repo}-{self.branch}"

    @property
    def os_tools_folder(self):
        return self.dest_folder / self.dest_folder_name


def copy_repo(
    repo: str,
    dest_folder: str,
    dest_folder_name,
    branch,
    subfolder,
):
    fl = FileLocation(
        dest_folder=dest_folder,
        dest_folder_name=dest_folder_name,
        repo=repo,
        branch=branch,
        subfolder=subfolder,
    )
    download(url=fl.url, dest_path=fl.zipfile)
    unzip(zip_store=fl.zipfile, dest_folder=fl.dest_folder)

    if fl.os_tools_folder.exists():
        shutil.rmtree(fl.os_tools_folder)
    shutil.move(fl.move_folder, fl.os_tools_folder)

    # Remove downloaded zip file and unzipped folder
    fl.zipfile.unlink()
    shutil.rmtree(fl.unzipped_folder)


def copy_os_tools(dest_folder: str, branch="main", subfolder="python"):
    REPO = "tools-onderzoek-en-statistiek"
    DEST_FOLDER_NAME = "ostools"
    if not branch:
        branch = "main"
    copy_repo(REPO, dest_folder, DEST_FOLDER_NAME, branch, subfolder)


if __name__ == "__main__":
    copy_os_tools("C:/python_projects/_uitproberen/test_project/src")
