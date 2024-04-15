import os
from io import BytesIO

from common.repository import IRepository
from common.s3_service import S3Service
from common.utils import find_extension
from structlog import get_logger

logger = get_logger()


class IOPRepository(IRepository):
    ZIPED_DIR = "raw/"
    EXTRACTED_DIR = "extracted/"

    def __init__(self) -> None:
        super().__init__()
        self.bucket = os.getenv("IOP_BUCKET_NAME", "iop")
        self.s3 = S3Service(self.bucket)

    def get_all_raw_filenames(self):
        return [
            f.key.removeprefix("raw/")
            for f in self.s3.objects.filter(Prefix=self.ZIPED_DIR).all()
        ]

    def find_all(self, filenames_to_process=None):
        grouped_files = {}
        filenames = (
            filenames_to_process
            if filenames_to_process
            else self.__find_all_extracted_files()
        )
        for file in filenames:
            last_part = os.path.basename(file)
            filename_without_extension = last_part.split(".")[0]
            if filename_without_extension not in grouped_files:
                grouped_files[filename_without_extension] = {}
            extension = find_extension(last_part)
            grouped_files[filename_without_extension][extension] = file
        return list(grouped_files.values())

    def get_by_id(self, id):
        retfile = BytesIO()
        self.s3.download_fileobj(id, retfile)
        return retfile

    def save(self, filename, obj):
        prefix = self.ZIPED_DIR if ".zip" in filename else self.EXTRACTED_DIR
        self.s3.upload_fileobj(obj, prefix + filename)

    def delete_all(self):
        self.s3.objects.all().delete()

    def __find_all_extracted_files(self):
        return [
            f.key
            for f in self.s3.objects.filter(Prefix=self.EXTRACTED_DIR).all()
            if self.is_meta(f.key) or ".pdf" in f.key
        ]

    def is_meta(self, filename):
        return ".xml" in filename
