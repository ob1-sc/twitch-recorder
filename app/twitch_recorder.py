from twitch_api import TwitchApi
import redis
import time
import os
import subprocess

twitch_channel = os.getenv("TWITCH_CHANNEL")
redis_host = os.getenv("REDIS_HOST", "localhost") 
redis_port = os.getenv("REDIS_PORT", 6379) 
redis_password = os.getenv("REDIS_PASSWORD", "")

twitch_client_id = os.getenv("TWITCH_CLIENT_ID") 
twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET") 

# login
api_helper = TwitchApi(twitch_client_id, twitch_client_secret)

request_params = {
    "user_login" : twitch_channel
}

# check if the user is online by checking the channel data
response = api_helper.get("https://api.twitch.tv/helix/streams", request_params)
channel_data = response.json().get("data")

if channel_data:

    try:

        r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

        # delete nested list as it can't be saved
        channel_data[0].pop("tag_ids")

        # check if we have an entry for the stream
        channel_entry = r.hgetall(channel_data[0].get("id"))

        # if no entry for the stream, make one and start recording
        if not channel_entry or ( channel_data[0].get("id") != channel_entry.get("id") ):

            print(f'Starting recording for - channel: {twitch_channel} - stream id: {channel_data[0].get("id")}')
            r.hmset(channel_data[0].get("id"), channel_data[0])

            recording_filename = "/recordings/" + twitch_channel + "-" + channel_data[0].get("id")

            # start streamlink process  
            subprocess.call(["streamlink", "twitch.tv/" + twitch_channel, "best", "-o", recording_filename + ".stream", "--hls-duration", "00:01:00"])

            print("Recording stream is done. Fixing video file.")
            subprocess.call(["ffmpeg", "-err_detect", "ignore_err", "-i", recording_filename + ".stream", "-c", "copy", recording_filename + ".mp4"])  
            os.remove(recording_filename + ".stream")  

    except Exception as e:
        print(e)