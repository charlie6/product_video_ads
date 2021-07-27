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

"""Application entrypoint."""

import os
import time
import flask

import video_generator.log
from video_generator.authentication.token_auth import TokenAuth
# Handle "events" from configuration
from video_generator.configuration.event_handler import EventHandler as EventHandler
from video_generator.configuration.spreadsheet_configuration import SpreadsheetConfiguration as Configuration
from video_generator.image.image_generator import ImageGenerator as ImageGenerator
# Handles image processing
from video_generator.image.image_processor import ImageProcessor as ImageProcessor
from video_generator.storage.cloud_storage_handler import CloudStorageHandler as CloudStorageHandler
from video_generator.storage.drive_storage_handler import DriveStorageHandler as StorageHandler
from video_generator.uploader.youtube_upload import YoutubeUploader as Uploader
from video_generator.video.video_generator import VideoGenerator as VideoGenerator
# Handles video processing
from video_generator.video.video_processor import VideoProcessor as VideoProcessor

logger = video_generator.log.getLogger()
app = flask.Flask("Product Video Ads")
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

@app.route('/', methods=['GET'])
def index():
    return flask.send_from_directory(static_path, 'index.html')

@app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
    return flask.send_from_directory(static_path, path)

@app.route('/generate_video')
def generate_video():
    # Read environment parameters
    #spreadsheet_id = os.environ.get('SPREADSHEET_ID')
    #bucket_name = os.environ.get('BUCKET_NAME')

    #if spreadsheet_id is None or bucket_name is None:
    #    print('Please set environment variable SPREADSHEET_ID and BUCKET_NAME')
    #    exit(1)

    #authenticator = TokenAuth(bucket_name, CloudStorageHandler())
    #credentials = None

    # Tries to retrieve token from storage each 5 minutes
    #while True:
    #    credentials = authenticator.authenticate()

    #    if credentials is not None:
    #        break

     #   logger.info('Sleeping for 5 minutes before trying again...')
     #   time.sleep(5 * 60)

    # Starts processing only after token authenticated!
    logger.info('[v2] Started processing...')

    # Dependencies
    #configuration = Configuration(spreadsheet_id, credentials)
    #storage = StorageHandler(configuration.get_drive_folder(), credentials)
    #cloud_storage = CloudStorageHandler(credentials)
    #video_processor = VideoProcessor(storage, VideoGenerator(), Uploader(credentials), cloud_storage)
    #image_processor = ImageProcessor(storage, ImageGenerator(), cloud_storage)

    VideoGenerator().process_video([],[],'test.mp4', 'output.mp4')

    # Handler acts as facade
    #handler = EventHandler(configuration, video_processor, image_processor)

    #while True:

        #try:

            # Sync drive files to local tmp
        #    storage.update_local_files()

            # Process configuration joining threads
        #    handler.handle_configuration()

        #except Exception as e:
        #    logger.error(e)

        # Sleep!
        #interval = configuration.get_interval_in_minutes()
        #logger.info('Sleeping for %s minutes', interval)
        #time.sleep(int(interval) * 60)


if __name__ == '__main__':
  # When running locally, disable OAuthlib's HTTPs verification.
  # ACTION ITEM for developers:
  #     When running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8080, debug=True)
