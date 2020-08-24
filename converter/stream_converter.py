import os
import subprocess
import redis
import time

redis_host = os.getenv("REDIS_HOST", "localhost") 
redis_port = os.getenv("REDIS_PORT", 6379) 
redis_password = os.getenv("REDIS_PASSWORD", "")

# wait 1 mins before attempting conversion
time.sleep(60)

# connect to redis
r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

# only convert streams while marker file exists
while os.path.exists("/shared/stream.id"):

    # read stream id from marker file
    with open("/shared/stream.id", "r") as f:
        stream_id = f.read()

    print(f'Starting conversion for stream: {stream_id}')

    # process all stream files
    while r.llen(stream_id + "-files") != 0:

        try:
            # get the next stream to convert
            stream_to_convert = r.lpop(stream_id + "-files")

            # call ffmpeg to clean up any errors in the stream file
            print(f'Converting following stream to mpeg: {stream_to_convert}')
            subprocess.call(["ffmpeg", "-err_detect", "ignore_err", "-i", stream_to_convert + ".stream", "-c", "copy", stream_to_convert + ".mp4"])  

            # clean up
            print('Cleaning up raw stream file')
            os.remove(stream_to_convert + ".stream")  

        except Exception as e:
            print(f'Error occured while converting stream: {e}')

    # wait 5 mins before processing
    time.sleep(300)