from typing import List

from google.cloud import exceptions, storage


class GoogleBucketHelper:

    def __init__(self, project_id: str) -> None:
        """Initializes the GoogleBucketHelper.

        Args:
            project_id: The Google Cloud project ID.
        """
        self.client = storage.Client(project=project_id)

    def upload_content(
        self,
        content: str,
        bucket_name: str,
        filename: str,
        content_type: str = "text/html",
    ) -> None:
        """Uploads a file to a Google Cloud Storage bucket.

        Args:
            content: The file content, e.g. a string or text
            bucket_name: The name of the bucket.
            filename: name of the file in the bucket.
            content_type: The content type of the file.
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_string(content, content_type=content_type)

    def download_as_text(self, bucket_name: str, path: str) -> str:
        """Reads a file from a Google Cloud Storage bucket and returns it as string

        Args:
            bucket_name: The name of the bucket.
            path: The path to the file in the bucket.
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(path)
        return blob.download_as_text()

    def exists_bucket(self, bucket_name: str) -> bool:
        """Checks if a Google Cloud Storage bucket exists.

        Args:
            bucket_name: The name of the bucket.

        Returns:
            True if the bucket exists, False otherwise.
        """
        try:
            self.client.get_bucket(bucket_name)
            return True
        except exceptions.NotFound:
            return False

    def list_all_files_in_bucket(
        self, bucket_name: str, folder_name: str, suffix: str = ""
    ) -> List[str]:
        """Lists all files in a Google Cloud Storage bucket.

        Args:
            bucket_name: The name of the bucket.
            folder_name: The name of the folder to list files from.
            suffix: Optional. A suffix to filter the files by.

        Returns:
            A list of file paths in the bucket.
        """
        bucket = self.client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=folder_name)
        files: List[str] = [blob.name for blob in blobs if blob.name.endswith(suffix)]
        return files
