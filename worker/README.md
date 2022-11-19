# Waveform Separation Worker

The steps you need to take:

+ Develop a Python program that listens to the `toWorkers` redis key exchange, receives a message and retrieves the MP3 song to separate.
+ Create a Docker image that can execute the DEMUCS software, run `min.io` clients and has access to a remote Redis database.

## Creating a worker image
The worker will use the [Facebook DEMUCS](https://github.com/facebookresearch/demucs/blob/main/demucs/separate.py)
software. This is an open-source waveform separation library that has Python bindings and good documentation. The software distribution requires Python 3.6 or above; installing Flair is as simple as executing:
```
pip install demucs
```
Installing flair installs many packages, produces a ~3.5GB container image. It takes a while to upload that to e.g. the `docker.io` registry.


To save time, you can [use an existing DEMUCS docker images](https://github.com/xserrat/docker-facebook-demucs) that is the container resulting from [this Dockerfile](https://github.com/xserrat/docker-facebook-demucs/blob/main/Dockerfile).

You can, but are not required to, use this as the base image for the image containing your worker code. Recall that you can extend a Docker image using `FROM`, then adding additional files and over-riding the `CMD` or `RUN` commands. That means you do *not* need to build the basic `flair` Docker container yourself and when you "push" your image to Docker hub, you should have to upload very little data because my base image has already been uploaded.
## Program to do Music Source Separation

You'll need a single Redis list data type to send data to the worker & another for logging. Redis uses numerical database numbers and number 0 is the default database. Each database is a "key-value" store meaning you can specify different keys for the worker queue (`toWorker` is a good key) and logging (`logging`).

You can use whatever method you like to get data from the REST API to the worker; my solution just sends JSON strings through the Redis queue.

Rather than send the large MP3 files through Redis, I suggest using the Min.io object storage system (or other object store) to store the song contents; see the [nodes in the overall README](../README.md).

If the `toWorker` request indicates that a *webhook callback* should be used, you should issue an HTTP POST request passing in the payload portion of the callback. You [can use the Python requests library](https://docs.python-requests.org/en/latest/user/quickstart/#make-a-request) to make that request. You don't need to do anything if the request fails, but you should be aware the request may fail.

## Waveform Separation Analysis

The [DEMUCS Docker image](https://github.com/xserrat/docker-facebook-demucs) has directions on how to generate a song, but you need to dig a little. The README indicate you can use
```
make run track=mysong.mp3
```
to convert a song -- but that invokes this command in the Makefile:
```
	docker run --rm -i \
		--name=demucs \
		-v $(current-dir)input:/data/input \
		-v $(current-dir)output:/data/output \
		-v $(current-dir)models:/data/models \
		xserrat/facebook-demucs:latest \
		"python3 -m demucs.separate --out /data/output \
		/data/input/$(track)"
```

The critical part is is `"python3 -m demucs.separate --out /data/output /data/input/$(track)"` -- this indicates that they are running the `demucs.separate` Python module with the supplied arguments. If you look at the [associated DEMUCS code](https://github.com/facebookresearch/demucs/blob/main/demucs/separate.py) you'll see you can also add an `--mp3` option to have the files written in MP3 format rather than WAV.

The DEMUCS program will leave the output in a directory with four files -- one for each track.
For example, if processing a file from `/tmp/{songhash}.mp3` with output directory `/tmp/output`, the
output files are in `/tmp/output/mdx_extra_q/{songhash}/{part}.mp3` where `{songhash}` is the unique identifier for the original song and `{part}` is one of `bass`, `drums`, `vocals` or `other`.

You would then retrieve those files and place them in the Min.io storage system using *e.g.* [fput_object](https://min.io/docs/minio/linux/developers/python/API.html) interface in the appropriate bucket.

Rather than trying to "call" the DEMUCS code from within my Python worker, I simply use the `os.system(....)` call to execute it as a separate program and then check that it worked. If you find that DEMUCS is failing, remember that it consumes ***a lot*** of RAM -- you might not have enough on your laptop or your Docker setup might be limiting what you can use.

## Debugging Support

At each step of your processing, you should log debug information using the logging infrastructure documented in [the logging directory](../logs/README).

When installing the `redis` library used to communicate with `redis`, you should use the `pip` or `pip3` command to install the packages. My solution used the following Python packages in addition to `demucs`
```
sudo pip3 install --upgrade minio redis requests
```

## Suggested Development Steps

When you actually run the text classifier, the existing 2.5GByte model will be downloaded from Germany. If you do this in a container or pod, this model will be repeatedly downloaded. This takes a while and it slows down your debug-edit cycle. If you do this on your laptop instead of in a container the downloaded model will be saved in your home directory.

Thus, we recommend that:
* Install the `demucs` Docker image on your laptop using the [existing Docker image](https://github.com/xserrat/docker-facebook-demucs).
* Deploy Redis and Min.io and the use the `kubectl port-forward` mechanism listed in the [corresponding README.md](../redis/README.md) file to expose those services on your local machine. We've [provided a script `deploy-local-dev.sh`](../deploy-local-dev.sh) for that purpose.
* Now that you are port-forwarding during development, you can run `worker-server.py` on your laptop and it will find the Redis/Minio ports on the localhost. 
* But, when you deploy your solution in Kubernetes, you'll need to tell `worker-server.py` what hosts to use when deployed; this should be done using environment variables in the deployment specification.
* Use the provided `log_info` and `log_debug` routines that write to the `logs` topic to simplify your development. You won't be able to figure out what is going on without logs. We've provided template code for that.
* Do your development by building a docker image that extends the [existing Docker image](https://github.com/xserrat/docker-facebook-demucs) with your server code and uses `os.system(...)` to run the demucs commands. 

Lastly, you should construct a program to send a sample request to your worker. We've [included one in send-request.py](./send-request.py) that uses the message format that my solution uses.

Following this process, you can debug the use of the `demucs` library and the interface to redis and minio. Once you have a functioning `worker-server.py` you can set it up in Kubernetes using a deployment.
