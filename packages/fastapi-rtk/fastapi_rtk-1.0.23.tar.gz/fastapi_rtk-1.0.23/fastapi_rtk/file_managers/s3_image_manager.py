from ..bases.file_manager import AbstractImageManager
from ..setting import Setting
from ..utils import lazy
from .s3_file_manager import S3FileManager

__all__ = ["S3ImageManager"]


class S3ImageManager(S3FileManager, AbstractImageManager):
    """
    S3ImageManager is a specialized S3FileManager for handling image files.
    It inherits from S3FileManager and implements AbstractImageManager.
    """

    allowed_extensions = lazy(lambda: Setting.IMG_ALLOWED_EXTENSIONS)
    max_file_size = lazy(lambda: Setting.IMG_MAX_SIZE)
