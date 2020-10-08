#!/bin/bash

# Copyright 2020 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

PROJECT_NAME=video-generator:latest

echo 'About to install Video Generator on Kubernetes Engine...'

echo -n 'Type the project name: '
read CLOUD_PROJECT_NAME

gcloud config set project $CLOUD_PROJECT_NAME
gcloud config list

# Enable APIs
echo 'Enabling APIs...'
gcloud services enable drive.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable youtube.googleapis.com
gcloud services enable storagetransfer.googleapis.com
gcloud services enable container.googleapis.com

# Create cluster
echo 'Creating cluster video-generator-cluster on Google Kubernetes Engine...'
gcloud container clusters create video-generator-cluster \
--num-nodes=1 \
--zone us-west1-a \
--no-enable-autoupgrade \
--scopes=https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/youtube.upload,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/devstorage.read_write

gcloud container clusters get-credentials \
--zone us-west1-a \
video-generator-cluster

sleep 5

# Get docker image
gsutil cp gs://product-video-ads/c/video-generator/video-generator.tar .
docker load -i video-generator.tar

PROJECT_ID=$(gcloud config list --format 'value(core.project)' 2>/dev/null)
#PROJECT_ID=${PROJECT_ID/:/\/}
IMAGE_NAME=gcr.io/${PROJECT_ID}/${PROJECT_NAME}

docker tag $PROJECT_NAME $IMAGE_NAME
docker push $IMAGE_NAME

# Install application to cluster
echo 'Apply application to cluster...'

gsutil cp gs://product-video-ads/c/video-generator/video-generator.yaml video-generator.yaml

echo -n 'Type the spreadsheet ID: '
read SPREADSHEET_ID
export SPREADSHEET_ID=$SPREADSHEET_ID

echo 'Create a OAuth client ID credential with type Other/Desktop, then press enter to continue...'
read

# Generate auth token
gsutil cp gs://product-video-ads/c/video-generator/authenticator.py authenticator.py
pip3 install google-auth-oauthlib==0.4.0
python3 authenticator.py

# Crete bucket for token
BUCKET_NAME=$(echo "${SPREADSHEET_ID}-token" | tr '[:upper:]' '[:lower:]')

# Uploads token there
gsutil mb -b on gs://$BUCKET_NAME/
echo "Created bucket $BUCKET_NAME to store token"
gsutil cp token gs://$BUCKET_NAME/

#echo -n 'Type the bucket name: '
#read BUCKET_NAME
export BUCKET_NAME=$BUCKET_NAME
export IMAGE_NAME=$IMAGE_NAME

envsubst < video-generator.yaml | kubectl apply -f -

echo 'Deploying video-generator to cluster...'

sleep 10

echo 'Done'