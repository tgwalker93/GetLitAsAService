import sys
import os
import redis
# import jsonpickle
# from PIL import Image
import base64
import io
from minio import Minio
import time
##
## Configure test vs. production
##

##
## Configure test vs. production
##
files_to_add=[]
while True:
    try:
        print("before rdis connection")
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
        GET_HOSTS_FROM = os.environ.get('GET_HOSTS_FROM') or 'dns'
        REDIS_MASTER_SERVICE_HOST = os.environ.get('REDIS_MASTER_SERVICE_HOST') or 'localhost'
        REDIS_MASTER_SERVICE_PORT = os.environ.get('REDIS_MASTER_SERVICE_PORT') or 6379
        REDIS_SLAVE_SERVICE_HOST = os.environ.get('REDIS_SLAVE_SERVICE_HOST') or 'localhost'
        REDIS_SLAVE_SERVICE_PORT = os.environ.get('REDIS_SLAVE_SERVICE_PORT') or 6379

        # redisClient = redis.StrictRedis(host=REDIS_MASTER_SERVICE_HOST, port=REDIS_MASTER_SERVICE_PORT, db=0)
        redisClient = redis.Redis(host=REDIS_MASTER_SERVICE_HOST, port=REDIS_MASTER_SERVICE_PORT, db=0)
        print("before minio connection")
        minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
        minioUser = os.getenv("MINIO_USER") or "rootuser"
        minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

        minioClient = Minio(minioHost,
                    secure=False,
                    access_key=minioUser,
                    secret_key=minioPasswd)    

        print("before calling queue")
        work = redisClient.blpop("queue", timeout=0)
        ##
        ## Work will be a tuple. work[0] is the name of the key from which the data is retrieved
        ## and work[1] will be the text log message. The message content is in raw bytes format
        ## e.g. b'foo' and the decoding it into UTF-* makes it print in a nice manner.
        ##
        # If work exists, then do some work
        #print(work)
        print("running")
        if work != None and len(work) > 1:
            print("work exists")
            nextJobString = work[1].decode('utf-8')
            nextJobList = nextJobString.split(":")
            #print(nextJobString)
            if len(nextJobList) == 2:
                print("nextjoblist is size 2")
                print(nextJobList[0])

                decoded_data=base64.b64decode(nextJobList[1])
                ioBuffer = io.BytesIO(decoded_data)
                result = minioClient.put_object("queue", nextJobList[0] + ".mp3", ioBuffer, len(decoded_data))

                #make sure that queue and output exist, if not then create new
                if not minioClient.bucket_exists('queue'):
                    print(f"Create bucket queue")
                    minioClient.make_bucket('queue')

                if not minioClient.bucket_exists('output'):
                    print(f"Create bucket queue")
                    minioClient.make_bucket('output')

                #list all buckets
                buckets = minioClient.list_buckets()

                for bucket in buckets:
                    print(f"Bucket {bucket.name}, created {bucket.creation_date}")
                    if bucket.name == "queue":
                        print("i found queue bucket")
                        for songInQueue in minioClient.list_objects('queue', recursive=True):
                            print("I am iterating through queue bucket")
                            print(songInQueue.object_name)
                            print(nextJobList[0])
                            #print(thing.object_name)
                            if songInQueue.object_name == (nextJobList[0] + ".mp3"):
                                #song = minioClient.get_object("queue", songInQueue.object_name)
                                files_to_add.append(songInQueue.object_name)
                                try:
                                    print(f"Add file {songInQueue.object_name} as object {songInQueue.object_name}")
                                    with open(songInQueue.object_name, 'wb') as f:
                                            f.write(decoded_data)                           
                                    files_to_add.append(nextJobList[0])
                                    print("before removing object")
                                    minioClient.remove_object("queue", songInQueue.object_name)
                                    os.system(f'python3 -m demucs.separate --out /output --mp3 {songInQueue.object_name}')
                                except:
                                    print("Error when adding files the first time")
        # ------------------------------
        if os.path.exists("../output"):
            print("output")
            if os.path.exists("../output/mdx_extra_q"):
                print("mdx_extra_q folder is there")
                if len(files_to_add) > 0:
                    while len(files_to_add) > 0:
                        file = files_to_add.pop(0)
                        print("file to process below")
                        print(file)
                        directory = '../output/mdx_extra_q/' + file
                        if os.path.exists(directory):
                            # iterate over files in
                            # that directory
                            for part_filename in os.listdir(directory):
                                f = os.path.join(directory, part_filename)
                                # checking if it is a file
                                if os.path.isfile(f):
                                    print("I found some output")
                                    print(f)
                                    minioClient.fput_object("output", file + "-" + part_filename, f, content_type="audio/mpeg")
            else:
                print("mdx/extra_q doesn't exist")

        else:
            print("no output folder found")
        #Check the output folder for any processed files

        sys.stdout.flush()
        time.sleep(10)
        



    except Exception as exp:
        print(f"Exception raised in worker loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()