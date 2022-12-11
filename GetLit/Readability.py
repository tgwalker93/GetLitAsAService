import os, shutil
import glob
from keras.preprocessing.text import Tokenizer
from keras_preprocessing.sequence import pad_sequences
import simplemma
import re
import csv


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

f = open(os.path.join('./','Rank.csv'), "w+")
f.close()

os.chdir('./profiles')

my_file = open("Wheelock.txt", "r")

data = my_file.readlines() 
reader = [line.strip() for line in data]

my_file.close()

print(os.getcwd())

os.chdir('../LatLib-Flat')

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

for txt in list(glob.glob("*.txt")):
    print(txt)
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
    import sys

    # print(Book)
    # print(reader)

    Same = list(set(Book) & set(reader))
    X = round((len(Same)/len(reader))*100,2)
    print(X)

    if X <= 10:
        X = 'Easy'
    elif X > 10 and X <= 20:
        X = 'Medium'
    else:
        X = 'Hard' 
    # data = [f'{txt}Lemma.txt',X]
    data = [txt,X]

    print(os.getcwd())
    with open(os.path.join('../','Rank.csv'),'a',encoding='utf8') as f:
        # fd.write(data)
        writer = csv.writer(f)

        # # write the header
        # writer.writerow(header)

        # write the data
        writer.writerow(data)

    # sys.exit()
