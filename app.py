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
import flask

from google.oauth2.credentials import Credentials

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

SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/devstorage.read_write']

logger = video_generator.log.getLogger()
app = flask.Flask("Product Video Ads")
static_path = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "static")
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
access_token = os.environ.get('ACCESS_TOKEN')
refresh_token = os.environ.get('REFRESH_TOKEN')
gcp_project = os.environ.get('GCP_PROJECT')


@app.route('/', methods=['GET'])
@app.route('/login', methods=['GET'])
@app.route('/products', methods=['GET'])
@app.route('/bases', methods=['GET'])
@app.route('/offer_types', methods=['GET'])
@app.route('/generate', methods=['GET'])
def index():
    return flask.send_from_directory(static_path, 'index.html')


@app.route('/generate_video', methods=['POST'])
def generate_video():
    credentials = None
    if (client_id == None or client_secret == None):
        return {"error": "Server was not configured properly, OAuth2 Client id/secret pair missing."}, 503

    # Read environment parameters
    spreadsheet_id = flask.request.form['spreadsheet_id']
    if (spreadsheet_id == None):
        return {"error": "Please provide the parameter 'spreadsheet_id' in the body of the request."}, 400

    # Reads token from Auth Header
    auth_header = flask.request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
        credentials = Credentials(
            token=auth_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri='https://accounts.google.com/o/oauth2/token',
            scopes=SCOPES)

    # If no auth was found, try from env vars
    if (credentials == None and access_token != None and refresh_token != None):
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri='https://accounts.google.com/o/oauth2/token',
            scopes=SCOPES)

    if (credentials == None):
        return {"error": "No access token found. Either use Authorization header or set up env vars" }, 400


    # Dependencies
    configuration = Configuration(spreadsheet_id, credentials)
    storage = StorageHandler(configuration.get_drive_folder(), credentials)
    cloud_storage = CloudStorageHandler(gcp_project, credentials)
    video_processor = VideoProcessor(
        storage, VideoGenerator(), Uploader(credentials), cloud_storage)
    image_processor = ImageProcessor(storage, ImageGenerator(), cloud_storage)

    # Handler acts as facade
    handler = EventHandler(configuration, video_processor, image_processor)

    try:
        # Sync drive files to local tmp
        storage.update_local_files()
        # Process configuration joining threads
        handler.handle_configuration()
    except Exception as e:
        logger.error(e)
        return {"error": str(e)}, 503
    return {"result": "videos processed successfully."}


@app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
    return flask.send_from_directory(static_path, path)


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    #os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run('localhost', 5055, debug=True)
