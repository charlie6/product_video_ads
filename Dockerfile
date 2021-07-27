FROM python:3.7.11-alpine3.14

# Unzip and ImageMagick dependencies
RUN apk update && apk add unzip imagemagick==7.0.11.13-r0

# FFMPEG dependencies
RUN apk update && apk add ffmpeg-libs==4.4-r1 ffmpeg==4.4-r1

# Build dependencies
RUN apk update && apk add build-base libffi-dev==3.3-r2

# Node dependencies
RUN apk update && apk add nodejs==14.17.3-r0 npm==7.17.0-r0

# Create empty folder to custom credentials mapping
RUN mkdir -p /credentials

## Backend
ADD requirements.txt /usr/src/app/requirements.txt
RUN python3 -m pip install -r /usr/src/app/requirements.txt

# Application code
ADD video_generator /usr/src/app/video_generator
ADD app.py /usr/src/app

## Frontend
ADD frontend /usr/src/frontend
WORKDIR /usr/src/frontend
RUN npm install
RUN npm run build
RUN cp -r /usr/src/frontend/dist /usr/src/app/static

# Install app
WORKDIR /usr/src/app

ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
