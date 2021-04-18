from twitch_api import TwitchApi
import redis
import time
import os
import subprocess
import datetime

now = datetime.datetime.now()

twitch_channel = os.getenv("TWITCH_CHANNEL")
redis_host = os.getenv("REDIS_HOST", "localhost") 
redis_port = os.getenv("REDIS_PORT", 6379) 
redis_password = os.getenv("REDIS_PASSWORD", "")

twitch_client_id = os.getenv("TWITCH_CLIENT_ID") 
twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET") 

request_params = {
    "user_login" : twitch_channel
}

# check if the user is online by checking the channel data
api_helper = TwitchApi(twitch_client_id, twitch_client_secret)
response = api_helper.get("https://api.twitch.tv/helix/streams", request_params)
channel_data = response.json().get("data")
print(channel_data)
if channel_data:

    try:
        
        stream_id = channel_data[0].get("id")

        # create a marker file that contains the stream id for use by sidecars
        with open("/shared/stream.id", "w") as f:
            f.write(stream_id)

        r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

        # delete nested list as it can't be saved
        channel_data[0].pop("tag_ids")

        # check if we have an entry for the stream
        channel_entry = r.hgetall(stream_id)

        # if no entry for the stream, make one and start recording
        if not channel_entry or (stream_id != channel_entry.get("id")):

            print(f'Starting recording for - channel: {twitch_channel} - stream id: {stream_id}')
            
            # record stream entry in DB to prevent stream being recorded again
            r.hmset(stream_id, channel_data[0])

            part = 0
            segment = 0
            stream_title = ""

            # keep recording in 30 min chunks until the stream is complete
            while channel_data:

                # double check that the stream id hasn't changed, if so stop recording
                if stream_id != channel_data[0].get("id"):
                    break

                # get the stream title and replace whitespace with underscores
                latest_stream_title = channel_data[0].get("title").replace(" ", "_")

                if latest_stream_title != stream_title:
                    part += 1 # when the title updates, increment the part
                    segment = 0 # when the title updates, reset the segement counter
                    stream_title = latest_stream_title
                else:
                    segment += 1 # if the title is the same then increment the segment

                # create the filename from the stream title and a counter (for the stream segment)
                recording_filename = "/streams/" + str(now.year) + "." + str(now.month).zfill(2) + "." + str(now.day).zfill(2) + "---" + str(part) + "." + str(segment).zfill(2) + "---" + stream_title

                print("Starting to record: " + recording_filename)

                # start streamlink process  
                try:
                    subprocess.call(["streamlink", "twitch.tv/" + twitch_channel, "best", "-o", recording_filename + ".stream", "--hls-duration", "00:30:00", "--twitch-disable-ads"])
                except Exception as e:
                    print(f'Error occured while running streamlink: {e}')

                # save the file to be converted
                r.rpush(stream_id + "-files", recording_filename)

                # call the twitch api to check if the channel is still online and to get the latest title
                api_helper = TwitchApi(twitch_client_id, twitch_client_secret)
                response = api_helper.get("https://api.twitch.tv/helix/streams", request_params)
                channel_data = response.json().get("data")

                retry = 0
                # if no response, wait 15 seconds and try again up to a maximum of 5 times
                while not channel_data and (retry <= 5) :

                    print(f'Checking if channel {twitch_channel} is still online, attempt: {retry}')
                    time.sleep(15)
                    response = api_helper.get("https://api.twitch.tv/helix/streams", request_params)
                    channel_data = response.json().get("data")
                    retry += 1

            print("Finished recording stream.")

            # wait until all stream recordings have been converted
            while r.llen(stream_id + "-files") != 0:
                print(f'Waiting for all stream recordings to be converted before exiting')
                time.sleep(300)

        else:
            print(f'Recording already in progress for - channel: {twitch_channel} - stream id: {stream_id}')

        # delete the shared marker file
        os.remove("/shared/stream.id")

    except Exception as e:
        print(e)

else:
    print(f'Channel: {twitch_channel} is not online')
