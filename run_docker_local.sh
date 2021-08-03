docker build -t product_video_ads .
docker run --env-file=local_env_vars.txt -p 5055:5055 -t product_video_ads