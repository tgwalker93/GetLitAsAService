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
        "response": "Profile is being analyzed. This will take roughly 5min."}
        log_info("analyze was sucessful.")
    except:
        log_debug("analyze had an error.")
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

# start flask app
app.run(host="0.0.0.0", port=5000)