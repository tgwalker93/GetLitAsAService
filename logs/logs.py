import sys
import os
import redis

##
## Configure test vs. production
##

##
## Configure test vs. production
##
# redisHost = os.getenv("REDIS_HOST") or "localhost"
# redisPort = os.getenv("REDIS_PORT") or 6379

# redisClient = redis.StrictRedis(host=redisHost, port=redisPort, db=0)

SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
GET_HOSTS_FROM = os.environ.get('GET_HOSTS_FROM') or 'dns'
REDIS_MASTER_SERVICE_HOST = os.environ.get('REDIS_MASTER_SERVICE_HOST') or 'localhost'
REDIS_MASTER_SERVICE_PORT = os.environ.get('REDIS_MASTER_SERVICE_PORT') or 6379
REDIS_SLAVE_SERVICE_HOST = os.environ.get('REDIS_SLAVE_SERVICE_HOST') or 'localhost'
REDIS_SLAVE_SERVICE_PORT = os.environ.get('REDIS_SLAVE_SERVICE_PORT') or 6379

# redisClient = redis.StrictRedis(host=REDIS_MASTER_SERVICE_HOST, port=REDIS_MASTER_SERVICE_PORT, db=0)
redisClient = redis.Redis(host=REDIS_MASTER_SERVICE_HOST, port=REDIS_MASTER_SERVICE_PORT, db=0)

while True:
    try:
        work = redisClient.blpop("logging", timeout=0)
        ##
        ## Work will be a tuple. work[0] is the name of the key from which the data is retrieved
        ## and work[1] will be the text log message. The message content is in raw bytes format
        ## e.g. b'foo' and the decoding it into UTF-* makes it print in a nice manner.
        ##
        print(work[1].decode('utf-8'))
    except Exception as exp:
        print(f"Exception raised in log loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()