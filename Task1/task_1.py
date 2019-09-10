# predefined parameters
MAX_SEQUENCE_LENGTH = 350
EMBEDDINGS_FILE_DIR = '~/EmbeddingsSets/' # replace by your file path
EMBEDDING_DIM = 300

# loading dataset
import json
import numpy as np
import os
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.engine.input_layer import Input
from keras.layers import Embedding, Conv1D, MaxPooling1D, Flatten, Dense
from keras.optimizers import Nadam
from keras.models import Model
from sklearn.model_selection import train_test_split
import keras.backend as K
import matplotlib.pyplot as plt
import random
import tensorflow as tf

# to run on GPU
# config = tf.ConfigProto()
# config.gpu_options.allow_growth = True
# session = tf.Session(config=config)

# loading embeddings vector set
embeddings_index = {}
word_index = {'<UNK>':1,}
index_to_word = {0:'',1: '<UNK>'}
index = 2

with open(os.path.join(EMBEDDINGS_FILE_DIR, 'word2vec-google-news.vec'), 'r', encoding='utf8') as f:

    for line in f:
        values = line.split()
        word = values[0]
        coefs = np.asarray(values[1:], dtype='float32')
        embeddings_index[index] = coefs
        word_index[word] = index
        index_to_word[index] = word
        index += 1

embedding_matrix = np.zeros((len(embeddings_index) + 2, EMBEDDING_DIM))
for index, vec in embeddings_index.items():
    embedding_matrix[index] = vec


# Loading labs data sets 
emw_dev_dataset = []
with open('emw_dev.json', 'r', encoding='utf8') as datafile:
    for line in datafile:
        emw_dev_dataset.append(json.loads(line))
random.shuffle(emw_dev_dataset)

emw_train_dataset = []
with open('emw_train.json', 'r', encoding='utf8') as datafile:
    for line in datafile:
        emw_train_dataset.append(json.loads(line))
random.shuffle(emw_train_dataset)


# Preprocessing data sets
def get_padded_dataset(dataset):
    labels = [ x['label'] for x in dataset]
    data = [ x['text'] for x in dataset]
    # Preprocessing text
    tokenizer = Tokenizer(oov_token='<UNK>')
    tokenizer.word_index = word_index
    data_seqs = tokenizer.texts_to_sequences(data)
    data_seqs_padded = pad_sequences(data_seqs, maxlen=MAX_SEQUENCE_LENGTH)
    labels = np.array(labels)
    return (data_seqs_padded, labels)


# Defining metric for evaluation during training
def f1_score(y_true, y_pred):

    c1 = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    c2 = K.sum(K.round(K.clip(y_pred, 0, 1)))
    c3 = K.sum(K.round(K.clip(y_true, 0, 1)))

    if c3 == 0:
        return 0

    precision = c1 / c2
    recall = c1 / c3
    f1_score = 2 * (precision * recall) / (precision + recall)
    return f1_score


# Preprocess training set
x_train_emw, y_train_emw = get_padded_dataset(emw_train_dataset)


# Preprocess development set
x_dev_emw, y_dev_emw = get_padded_dataset(emw_dev_dataset)


# Modeling Our Network
sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
embedding_layer = Embedding(len(embeddings_index) + 2,
                            EMBEDDING_DIM,
                            weights=[embedding_matrix],
                            input_length=MAX_SEQUENCE_LENGTH,
                            trainable=False)
embedded_sequences = embedding_layer(sequence_input)
x = Conv1D(32, 5, padding='valid', activation='relu')(embedded_sequences)
x = MaxPooling1D(3)(x)
x = Conv1D(32, 4, padding='valid', activation='relu')(x)
x = MaxPooling1D(3)(x)
x = Conv1D(64, 3, padding='valid', activation='relu')(x)
x = MaxPooling1D(3)(x)
x = Flatten()(x)
x = Dense(64, activation='relu')(x)
preds = Dense(1, activation='sigmoid')(x)

model = Model(sequence_input, preds)


# Setting training parameters
learning_rate = 0.0005
epoch_num = 10
opt = Nadam(lr=learning_rate)
model.compile(loss='binary_crossentropy', optimizer=opt, metrics=['binary_accuracy', f1_score])


# Train the network model
history = model.fit(x_train_emw, y_train_emw,
                    epochs=epoch_num,
                    batch_size=64,
                    validation_data=(x_dev_emw, y_dev_emw)
                    )


# Plotting loss and accuracy curves using matplotlib
acc = history.history['binary_accuracy']
val_acc = history.history['val_binary_accuracy']
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(acc) + 1)

plt.plot(epochs, acc, 'bo', label='Training acc')
plt.plot(epochs, val_acc, 'b', label='Validation acc')
plt.title('Training and validation acc')
plt.xlabel('Epochs')
plt.ylabel('Acc')
plt.legend()
plt.show()

plt.plot(epochs, loss, 'bo', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

# # Make predictions for india and china test sets
# def predict_file(infile, outfile):
#     rows = []
#     with open(infile, 'r', encoding='utf8') as datafile:
#         for line in datafile:
#             rows.append(json.loads(line))

#     data = [ x['text'] for x in rows]
#     tokenizer = Tokenizer(oov_token ='<UNK>')
#     tokenizer.word_index = word_index
#     data_seqs = tokenizer.texts_to_sequences(data)
#     data_seqs_padded = pad_sequences(data_seqs, maxlen=MAX_SEQUENCE_LENGTH)
#     predictions = model.predict(data_seqs_padded)
#     with open(outfile, 'w') as outfile:
#         for i, prediction in enumerate(predictions):
#             outfile.write(str(rows[i]['id']) + '\t' + str(1 if prediction >= 0.5 else 0) + '\n')


# predict_file('emw_test.json', 'task1_test.predict')
# predict_file('emw_china.json', 'china_test_task1.predict')

