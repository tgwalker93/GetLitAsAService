#!/usr/bin/env python3

##
## Sample Flask REST server implementing two methods
##
## Endpoint /api/image is a POST method taking a body containing an image
## It returns a JSON document providing the 'width' and 'height' of the
## image that was provided. The Python Image Library (pillow) is used to
## proce#ss the image
##
## Endpoint /api/add/X/Y is a post or get method returns a JSON body
## containing the sum of 'X' and 'Y'. The body of the request is ignored
##
##
import sys
import os
import redis

from flask import Flask, request, Response, send_file, make_response
import jsonpickle
# from PIL import Image
import base64
# import io
# import numpy as np
import hashlib
from minio import Minio
import platform


##
## Configure test vs. production
##

##
## Configure test vs. production
##
SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
GET_HOSTS_FROM = os.environ.get('GET_HOSTS_FROM') or 'dns'
REDIS_MASTER_SERVICE_HOST = os.environ.get('REDIS_MASTER_SERVICE_HOST') or 'localhost'
REDIS_MASTER_SERVICE_PORT = os.environ.get('REDIS_MASTER_SERVICE_PORT') or 6379
REDIS_SLAVE_SERVICE_HOST = os.environ.get('REDIS_SLAVE_SERVICE_HOST') or 'localhost'
REDIS_SLAVE_SERVICE_PORT = os.environ.get('REDIS_SLAVE_SERVICE_PORT') or 6379

# redisClient = redis.StrictRedis(host=REDIS_MASTER_SERVICE_HOST, port=REDIS_MASTER_SERVICE_PORT, db=0)
redisClient = redis.Redis(host=REDIS_MASTER_SERVICE_HOST, port=REDIS_MASTER_SERVICE_PORT, db=0)


minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

minioClient = Minio(minioHost,
            secure=False,
            access_key=minioUser,
            secret_key=minioPasswd) 

# Initialize the Flask application
app = Flask(__name__)

# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.DEBUG)

infoKey = "{}.rest.info".format(platform.node())
debugKey = "{}.rest.debug".format(platform.node())
def log_debug(message, key=debugKey):
    print("DEBUG:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{debugKey}:{message}")

def log_info(message, key=infoKey):
    print("INFO:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{infoKey}:{message}")


def lemma_count(words):
    lemma_dict = {}
    for item in words:
        if item not in lemma_dict:
            lemma_dict[item] = 1
        else:
            lemma_dict[item] += 1
    
    lc = clean_lemma_counts(sorted(lemma_dict.items(), key=lambda kv: kv[1], reverse=True))
    return lc
    
def clean_lemma_counts(lemma_counts):
    lc = [] # new list of tuples with lemma and count
    non_use = []
    for lemma, count in lemma_counts:
        if((re.search(r'[^\w\s]', lemma))): #checks if there is punc
            non_use.append(lemma)
        else: # if no punc, add to new list
            new_tup = (lemma, count)
            lc.append(new_tup)
            
    # print(len(non_use)) # keeps track of how many lemmas we are removing
    return lc 


@app.route('/', methods=['GET'])
def hello():
    return '<h1> GetLit Server</h1><p> Use a valid endpoint </p>'

@app.route('/apiv1/analyze/<string:profileName>', methods=['GET'])
def analyze(profileName):
    log_info("analyze was called.")
    response = {"error": "An error has occured."}
    try:
        print(profileName)
        log_info("Profile received in Analyze method: " + profileName)
        redisClient.lpush('queue', f"{profileName}")
        response = { "profileName": profileName,
        "reason": "Profile is being analyzed. This will take roughly 5min."}
        log_info("analyze was sucessful.")
    except:
        log_debug("analyze had an error.")
        response = {"error": "An error has occured."}
    response = jsonpickle.encode(response)
    return Response(response=response, status=200, mimetype="application/json")

@app.route('/apiv1/separate', methods=['POST'])
def separate():
    print("i'm in the separate function")
    response = {"error": "An error has occured."}
    try:
        requestObj = jsonpickle.decode(request.data)
        print("below is data")   
        print(requestObj['callback'])   
        print(requestObj['callback']['data']['mp3'])
        songName = requestObj['callback']['data']['mp3']
        base64File = requestObj['mp3']
        songNameHash = hashlib.sha256(songName.encode('utf-8')).hexdigest()
        print(songNameHash)
        redisClient.lpush('queue', f"{songNameHash}:{base64File}")
        response = { "hash": songNameHash,
        "reason": "Song enqueued for separation"}
    except:
        response = {"error": "An error has occured."}
    response = jsonpickle.encode(response)
    return Response(response=response, status=200, mimetype="application/json")



@app.route('/apiv1/queue', methods=['GET'])
def queue():
    print("i'm in the queue function")
    log_info("queue was called.")
    error = ""
    try:
        queueData = [ x.decode('utf-8') for x in redisClient.lrange("queue", 0, -1) ]
        listOfQueues = []
        for q in queueData:
            listOfQueues.append(q)

        response = { "queue": listOfQueues}
        log_info("queue was sucessful.")
    except:
        log_info("queue has failed.")
        response = {"error": error}
    response = jsonpickle.encode(response)
    return Response(response=response, status=200, mimetype="application/json")

@app.route('/apiv1/track/<string:songName>', methods=['GET'])
def track(songName):
    songFound = False
    response = {"error": "An error has occured."}
    decoded_data = None
    log_info("Get track was called.")
    try:
        print('before i iterate through minio')
        log_info("before i iterate through minio")
        for songInOutput in minioClient.list_objects('output', recursive=True):
            print("I am iterating through output bucket")
            #print(thing.object_name)
            if songInOutput.object_name == songName:
                    songFound = True
                    #decoded_data=base64.b64decode(songInOutput.binary)              
                    minioClient.fget_object("output", songInOutput.object_name, songInOutput.object_name)
                    file = open(songInOutput.object_name, 'rb')
                    decoded_data = file.read()            
        if songFound == False:
            response = { "songName": songName, "message": "I could not find a song with the given song name."}
    except:
        response = {"error": "An error has occured."}
    if songFound == False:
        response = jsonpickle.encode(response)
        return Response(response=response, status=200, mimetype="application/json")
    else:
        response = make_response(decoded_data)
        response.headers.set('Content-Type', 'audio/mpeg')
        response.headers.set(
            'Content-Disposition', 'attachment', filename=songName + '.mp3')
        return response
            
@app.route('/apiv1/remove/<string:songName>', methods=['GET'])
def remove(songName):
    songFound = False
    response = {"error": "An error has occured."}
    try:
        print('before i iterate through minio')
        for songInOutput in minioClient.list_objects('output', recursive=True):
            print("I am iterating through output bucket")
            #print(thing.object_name)
            if songInOutput.object_name == songName:
                songFound = True
                minioClient.remove_object("output", songInOutput.object_name)
        if songFound:
            response = { "songName": songName, "message": "The song was successfully deleted."}
        else:
            response = { "songName": songName, "message": "I could not find a song with the given name."}
    except:
        response = {"error": "An error has occured."}
    response = jsonpickle.encode(response)
    return Response(response=response, status=200, mimetype="application/json")

# start flask app
app.run(host="0.0.0.0", port=5000)