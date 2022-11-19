#!/usr/bin/env python3
from __future__ import print_function
import requests
import json
import time
import sys
import base64
import jsonpickle
import random


def doAdd():
    print('im in do add')
    headers = {'content-type': 'application/json'}
    # send http request with image and receive response
    #add_url = "http://localhost:5000" + "/apiv1/remove/7db802f81935c32770efa65ecc98d35080082730f62ebff9ef669ae2226ae1ff"
    add_url = "http://localhost:5000" + "/apiv1/queue"
    response = requests.get(add_url, headers=headers)
    # decode response
    print("Response is", response)
    print(json.loads(response.text))


if __name__ == "__main__":
    # if len(sys.argv) < 3:
    #     print(f"Usage: {sys.argv[0]} <server ip> <cmd> <reps>")
    #     print(f"where <cmd> is one of add, rawImage, sum or jsonImage")
    #     print(f"and <reps> is the integer number of repititions for measurement")

    #Code below is for testing a single method in debug mode in google console
    if sys.argv[1] == 'add':
        doAdd()
