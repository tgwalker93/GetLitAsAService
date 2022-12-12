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

import os, shutil
import glob
from keras.preprocessing.text import Tokenizer
from keras_preprocessing.sequence import pad_sequences
import simplemma
import re
import csv
import sys
import platform

##
## Configure test vs. production
##
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

print("before rdis connection")
SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
GET_HOSTS_FROM = os.environ.get('GET_HOSTS_FROM') or 'dns'
REDIS_MASTER_SERVICE_HOST = os.environ.get('REDIS_MASTER_SERVICE_HOST') or 'localhost'
REDIS_MASTER_SERVICE_PORT = os.environ.get('REDIS_MASTER_SERVICE_PORT') or 6379
REDIS_SLAVE_SERVICE_HOST = os.environ.get('REDIS_SLAVE_SERVICE_HOST') or 'localhost'
REDIS_SLAVE_SERVICE_PORT = os.environ.get('REDIS_SLAVE_SERVICE_PORT') or 6379

# redisClient = redis.StrictRedis(host=REDIS_MASTER_SERVICE_HOST, port=REDIS_MASTER_SERVICE_PORT, db=0)
redisClient = redis.Redis(host=REDIS_MASTER_SERVICE_HOST, port=REDIS_MASTER_SERVICE_PORT, db=0)

infoKey = "{}.worker.info".format(platform.node())
debugKey = "{}.worker.debug".format(platform.node())
def log_debug(message, key=debugKey):
    print("DEBUG:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{debugKey}:{message}")

def log_info(message, key=infoKey):
    print("INFO:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{infoKey}:{message}")


print("before minio connection")
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

minioClient = Minio(minioHost,
            secure=False,
            access_key=minioUser,
            secret_key=minioPasswd)     

files_to_add=[]
currentFileNum = 1
while True:
    try:  

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
            currentDirectory = os.getcwd()

            print("current directory: " + currentDirectory)

            if "profiles" in currentDirectory or "LatLib-Flat" in currentDirectory:
                os.chdir('../')
            #The profile name
            nextJobString = work[1].decode('utf-8')
            log_info("Found a job! Next job in queue: " + nextJobString)
            print("Next job below")
            print(nextJobString)
            folder = './Lemma'
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
                    log_debug('Failed to delete %s. Reason: %s' % (file_path, e))

            folder = './Lemma-train'
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
                    log_debug('Failed to delete %s. Reason: %s' % (file_path, e))

            f = open(os.path.join('./','Rank.csv'), "w+")
            f.close()

            os.chdir('./profiles')
            
            #Wheelock.txt
            my_file = open(nextJobString+".txt", "r")

            data = my_file.readlines() 
            reader = [line.strip() for line in data]

            my_file.close()

            print(os.getcwd())
            log_info("Current directory in worker: " + os.getcwd())
            os.chdir('../LatLib-Flat')
            count = 1
            for txt in list(glob.glob("*.txt")):
            
                print(txt)
                log_info("Ranking File #" + str(count) + " -----------------------------")
                log_info("Ranking " + txt)
                in_file = open(txt, 'r',encoding='utf8')
                texts = in_file.read().splitlines()


                tokenizer = Tokenizer()
                tokenizer.fit_on_texts(texts)

                vocab_size = len(tokenizer.word_index) + 1

                temp = tokenizer.word_index

                in_file.close()

                temp = list(temp.keys())
                    
                # mytokens = ['Hier', 'sind', 'Vaccines']
                myLemma = []
                for token in temp:
                    myLemma.append(simplemma.lemmatize(token, lang='la'))

                lemma_counts = lemma_count(myLemma)

                Book = []

                for i in range(len(lemma_counts)):

                    Book.append(lemma_counts[i][0])

                with open(os.path.join('../Lemma',f'{txt}Lemma.txt'), "w", encoding='utf8') as f:
                    for t in lemma_counts:   
                        f.write(' '.join(str(s) for s in t) + '\n')

                with open(os.path.join('../Lemma-train',f'{txt}Lemma.txt'), "w",encoding='utf8') as f:
                    for t in Book:   
                        f.write(f"{t}\n")

                # print(Book)
                # print(reader)

                Same = list(set(Book) & set(reader))
                X = round((len(Same)/len(reader))*100,2)
                print(X)
                log_info("Score of " + txt + " is " + str(X))
                if X <= 10:
                    X = 'Easy'
                elif X > 10 and X <= 20:
                    X = 'Medium'
                else:
                    X = 'Hard' 
                # data = [f'{txt}Lemma.txt',X]
                data = [txt,X]

                print(os.getcwd())
                log_info("Adding score to Rank.csv")
                try:
                    
                    with open(os.path.join('../','Rank.csv'),'a') as f:
                        # fd.write(data)
                        writer = csv.writer(f)

                        # # write the header
                        # writer.writerow(header)

                        # write the data
                        writer.writerow(data)
                except Exception as exp:
                    print(f"Exception raised in worker loop: {str(exp)}")
                    log_debug(f"Exception raised in worker loop: {str(exp)}")
                count = count + 1

            log_info("The CSV is complete! Total count of files in library: " + str(count))
            log_info("Checking if output bucket exists.")
            if not minioClient.bucket_exists('output'):
                print(f"Create bucket output")
                log_info("output bucket doesn't exist. Creating buckuet.")
                minioClient.make_bucket('output')  
            os.chdir('../')
            log_info("Adding Results.csv to output bucket.")
            minioClient.fput_object("output", "Rankings"+str(currentFileNum)+".csv", os.getcwd() + "/Rank.csv", content_type="text/csv")
            currentFileNum = currentFileNum + 1
        sys.stdout.flush()
        time.sleep(10)
    
    except Exception as exp:
        print(f"Exception raised in worker loop: {str(exp)}")
        log_debug(f"Exception raised in worker loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()