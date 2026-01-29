import typing

from ..bases.file_manager import AbstractFileManager
from ..setting import Setting
from ..utils import T, lazy, smart_run, use_default_when_none

__all__ = ["S3FileManager"]


class S3FileManager(AbstractFileManager):
    """
    FileManager for handling files in S3 buckets.
    """

    allowed_extensions = lazy(lambda: Setting.FILE_ALLOWED_EXTENSIONS)
    max_file_size = lazy(lambda: Setting.FILE_MAX_SIZE)
    ERROR_CODE_FILE_NOT_FOUND = "NoSuchKey"

    def __init__(
        self,
        base_path: str | None = None,
        allowed_extensions: list[str] | None = None,
        max_file_size: int | None = None,
        namegen: typing.Callable[[str], str] | None = None,
        permission: int | None = None,
        bucket_name: str | None = None,
        bucket_subfolder: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        open_params: dict[str, typing.Any] | None = None,
        boto3_client: typing.Any | None = None,
        boto3_args: tuple[typing.Any, ...] | None = None,
        boto3_kwargs: dict[str, typing.Any] | None = None,
    ):
        """
        Initializes the S3FileManager.

        Args:
            base_path (str | None, optional): URL path to the S3 bucket. Defaults to None.
            allowed_extensions (list[str] | None, optional): Allowed file extensions. Defaults to None.
            max_file_size (int | None, optional): Maximum file size allowed. Defaults to None.
            namegen (typing.Callable[[str], str] | None, optional): Callable for generating file names. Defaults to None.
            permission (int | None, optional): File permission settings. Defaults to None.
            bucket_name (str | None, optional): Name of the S3 bucket. Defaults to None.
            bucket_subfolder (str | None, optional): Subfolder within the S3 bucket. Defaults to None.
            access_key (str | None, optional): AWS access key. Needed for default boto3 client in order to delete files. Defaults to None.
            secret_key (str | None, optional): AWS secret key. Needed for default boto3 client in order to delete files. Defaults to None.
            open_params (dict[str, typing.Any] | None, optional): Parameters for opening files. Defaults to None.
            boto3_client (typing.Any | None, optional): Boto3 client instance. If None, a new client will be created. Defaults to None.
            boto3_args (tuple[typing.Any, ...] | None, optional): Positional arguments for boto3 client creation. Defaults to None.
            boto3_kwargs (dict[str, typing.Any] | None, optional): Keyword arguments for boto3 client creation. Defaults to None.
        Raises:
            ImportError: If required libraries are not installed.
        """
        super().__init__(
            base_path, allowed_extensions, max_file_size, namegen, permission
        )

        try:
            import boto3
            import botocore
            import botocore.client
            import smart_open

            self.smart_open = smart_open
            self.boto3 = boto3
            self.botocore = botocore
            self.botocore.client = botocore.client
        except ImportError:
            raise ImportError(
                "smart_open is required for S3FileManager. "
                "Please install it with 'pip install smart_open[s3]'."
            )

        self.bucket_name = bucket_name
        self.bucket_subfolder = bucket_subfolder
        self.access_key = access_key
        self.secret_key = secret_key
        self.open_params = open_params or {}
        boto3_args = use_default_when_none(boto3_args, ("s3",))
        boto3_kwargs = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            **(boto3_kwargs or {}),
        }
        self.boto3_client = boto3_client or self.boto3.client(
            *boto3_args, **boto3_kwargs
        )

        if not self.bucket_name:
            raise ValueError(
                f"Bucket name must be provided for {self.__class__.__name__}"
            )

        if not self.access_key:
            raise ValueError(
                f"Access key must be provided for {self.__class__.__name__}"
            )
        if not self.secret_key:
            raise ValueError(
                f"Secret key must be provided for {self.__class__.__name__}"
            )

    def get_path(self, filename):
        return self.base_path + "/" + filename

    def get_file(self, filename):
        with self.smart_open.open(
            self.get_path(filename), "rb", **self.open_params
        ) as f:
            return f.read()

    async def stream_file(self, filename):
        with self.smart_open.open(
            self.get_path(filename), "rb", **self.open_params
        ) as f:
            while chunk := await smart_run(f.read, 8192):
                yield chunk

    def save_file(self, file_data, filename):
        path = self.get_path(filename)
        with self.smart_open.open(path, "wb", **self.open_params) as f:
            f.write(file_data.file.read())
        return path

    def save_content_to_file(self, content, filename):
        path = self.get_path(filename)
        with self.smart_open.open(path, "wb", **self.open_params) as f:
            f.write(content)
        return path

    def delete_file(self, filename):
        if self.file_exists(filename):
            self.boto3_client.delete_object(
                Bucket=self.bucket_name,
                Key=f"{self.bucket_subfolder}/{filename}"
                if self.bucket_subfolder
                else filename,
            )

    def file_exists(self, filename):
        path = self.get_path(filename)
        try:
            with self.smart_open.open(path, "rb", **self.open_params) as f:
                f.read(1)  # Try to read a byte to confirm existence
            return True
        except IOError as e:
            return self._handle_io_error(e, value_to_return=False)

    def get_instance_with_subfolder(self, subfolder, *args, **kwargs):
        return super().get_instance_with_subfolder(
            subfolder,
            bucket_name=self.bucket_name,
            bucket_subfolder=f"{self.bucket_subfolder}/{subfolder}"
            if self.bucket_subfolder
            else subfolder,
            access_key=self.access_key,
            secret_key=self.secret_key,
            open_params=self.open_params,
            boto3_client=self.boto3_client,
            *args,
            **kwargs,
        )

    def _handle_io_error(self, e: IOError, *, value_to_return: T = None):
        if hasattr(e, "backend_error") and isinstance(
            e.backend_error, self.botocore.client.ClientError
        ):
            error = e.backend_error.response.get("Error", {})
            error_code = error.get("Code")
            if error_code == self.ERROR_CODE_FILE_NOT_FOUND:
                return value_to_return
        raise e
