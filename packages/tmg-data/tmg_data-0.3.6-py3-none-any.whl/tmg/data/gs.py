from google.cloud import storage
from tmg.data.auth import get_credentials

class Client:
    """
    Client to bundle Google Storage functionality.

    Args:
        project (str): The Project ID for the project which the client acts on behalf of.
        credentials (optional): Google Cloud credentials to use. If not provided, uses default credentials.
    """

    def __init__(self, project, credentials=None):
        self.project = project

        if credentials is None:
            credentials = get_credentials()

        self.credentials = credentials
        self.storage_client = storage.Client(project=project, credentials=credentials)

    def download(self, gs_uri, destination_file_name):
        """Download from Google Storage to local.

        Args:
            gs_uri (str):  The Google Storage uri. For example: ``gs://my_bucket_name/my_filename``.
            destination_file_name (str):  The destination file name. For example: ``/some_path/some_file_name``.
        """

        with open(destination_file_name, 'wb') as file_obj:
            self.storage_client.download_blob_to_file(gs_uri, file_obj)

    def upload(self, source_file_name, bucket_name, blob_name):
        """Upload from local to Google Storage.

        Args:
            source_file_name (str):  The source file name.
            bucket_name (str):  The Google Storage bucket name.
            blob_name (str): The destination file name in the bucket
        """

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(source_file_name)

    def create(self, bucket_name):
        """create a bucket in Google Storage.

        Args:
            bucket_name (str):  The Google Storage bucket name.
        """

        self.storage_client.create_bucket(bucket_name, location='EU')

    def list_blobs(self, bucket_name, prefix=None):
        """List all blobs in a bucket with a prefix.

        Args:
            bucket_name (str):  The Google Storage bucket name.
            prefix (str):  The prefix to filter the blobs. None means no filter.

        Returns:
            list: List of blobs.
        """
    
        bucket = self.storage_client.bucket(bucket_name)
        return list(bucket.list_blobs(prefix=prefix))
    
    def delete_blob(self, bucket_name, blob_name):
        """Delete a blob in a bucket.

        Args:
            bucket_name (str):  The Google Storage bucket name.
            blob_name (str):  The blob name.
        """

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()

    def delete_bucket(self, bucket_name, force=False):
        """Delete a bucket in Google Storage.

        Args:
            bucket_name (str): The Google Storage bucket name.
            force (bool, optional): Enforce deletion if bucket is not empty. Defaults to False.
        """

        bucket = self.storage_client.bucket(bucket_name)
        bucket.delete(force=force)