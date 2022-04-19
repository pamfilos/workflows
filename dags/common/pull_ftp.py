import io
import zipfile

from common.repository import IRepository
from common.sftp_service import SFTPService


def migrate_from_ftp(sftp: SFTPService, repo: IRepository):
    filenames = sftp.list_files()
    for file in filenames:
        file_bytes = sftp.get_file(file)
        with zipfile.ZipFile(file_bytes) as zip:
            for zip_filename in zip.namelist():
                file_prefix = file.split(".")[0]
                file_content = zip.read(zip_filename)
                repo.save(file_prefix + "/" + zip_filename, io.BytesIO(file_content))
        repo.save(file, file_bytes)


def trigger_file_processing(repo: IRepository):
    files = repo.find_all()
    for file in files:
        print("Starting a new dag to process the following file :", file)
        # TODO: Run new Dag to process the file.
    return files
