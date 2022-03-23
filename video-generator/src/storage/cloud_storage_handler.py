# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import google.auth
from google.cloud import storage

import log

API_SCOPES = [
    'https://www.googleapis.com/auth/devstorage.read_write'
]


class CloudStorageHandler():
    logger = log.getLogger()

    def __init__(self, project: str = None, credentials=None, gcs_bucket_name=None):
        if credentials is None:
            # Obtains Service Account from environment just to access storage
            # It comes from GCP or GOOGLE_APPLICATION_CREDENTIALS env variable file
            credentials, project = google.auth.default(scopes=API_SCOPES)

        self.storage_client = storage.Client(
            project=project, credentials=credentials)
        self.gcs_bucket_name = gcs_bucket_name

    def download_string(self, bucket_name, object_name):
        return self.storage_client.get_bucket(bucket_name).blob(object_name).download_as_string()

    def download_file_to_path(self, bucket_name, object_name, destination_path):
        self.logger.debug(
            'Downloading from bucket %s file %s and saving to %s' % (bucket_name, object_name, destination_path))
        self.storage_client.get_bucket(bucket_name).blob(object_name).download_to_filename(destination_path)

    def upload_to_preview(self, output_file_path):
        if not self.gcs_bucket_name:
            raise ValueError('Cannot upload to preview to gcs due to gcs_bucket_name=None.')

        title = output_file_path.split('/')[-1]
        bucket = self.storage_client.bucket(self.gcs_bucket_name)
        blob = bucket.blob(title)
        blob.upload_from_filename(output_file_path)
        self.logger.info('Uploaded preview video %s to gcs bucket %s', title, self.gcs_bucket_name)
        return f"gs://{self.gcs_bucket_name}/{title}"

    def sanitize_bucket_name(self, bucket_name):
        # Convert all letters to lowercase
        bucket_name = bucket_name.lower()
        # Only allow letters, numbers, dashes and underscore
        return ''.join(char for char in bucket_name if (char.isalnum() or char == '-' or char == '_'))

    def sanitize_object_name(self, string):
        # Only allow letters, numbers, dashes, underscores, and slashes (to create directories)
        return ''.join(char for char in string if (char.isalnum() or char == '-' or char == '_' or char == '/'))

    def create_bucket_if_not_exists(self, bucket_name):
        if not storage.Bucket(self.storage_client, bucket_name).exists():
            bucket = self.storage_client.bucket(bucket_name)
            bucket.storage_class = "STANDARD"
            return self.storage_client.create_bucket(bucket, location="us")
        else:
            return self.storage_client.bucket(bucket_name)

    def upload_to_directory(self, output_file_path, config):
        bucket_name = self.sanitize_bucket_name(config.get('custom_dir'))
        if not bucket_name:
            raise ValueError('Directory name cannot be empty when calling upload_to_directory.')

        bucket = self.create_bucket_if_not_exists(bucket_name)

        name = self.sanitize_object_name(config.get('name', ''))
        timestamp = output_file_path.split('/')[-1]
        object_name = f"{name}_{timestamp}"
        blob = bucket.blob(object_name)
        blob.upload_from_filename(output_file_path)
        self.logger.info('Uploaded file %s to directory %s', object_name, bucket)
        return f"gs://{bucket}/{object_name}"