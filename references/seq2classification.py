import pdb

from keras import Input, Model
from keras.layers import Dense
from keras.layers import Embedding
from keras.layers import LSTM
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer

# define documents
from Preprocessing import *

latent_dim = 256
batch_size = 64
epochs = 1

data_set = loadData()
train, test = getTrainTest(data_set)
# prepare tokenizer
t = Tokenizer()
t.fit_on_texts(train['x_term'])
num_encoder_tokens = len(t.word_index) + 1

# integer encode the documents
encoded_docs = t.texts_to_sequences(train['x_term'])

# pad documents to a max length of 4 words
max_length = 1000
padded_docs = pad_sequences(encoded_docs, maxlen=max_length, padding='post')
print(padded_docs)

labels = train["y_term"]
num_decoder_tokens = 8

# Define an input sequence and process it.
encoder_inputs = Input(shape=(None,))
encoder_embedding_layer = Embedding(num_encoder_tokens, latent_dim)(encoder_inputs)
encoder_lstm_layer, state_h, state_c = LSTM(latent_dim, return_state=True)(encoder_embedding_layer)
encoder_states = [state_h, state_c]

# Set up the decoder, using `encoder_states` as initial state.
decoder_inputs = Input(shape=(None, 8))
decoder_lstm = LSTM(latent_dim, return_sequences=True,return_state=True)
decoder_lstm_layer,_,_ = decoder_lstm(decoder_inputs, initial_state=encoder_states)
decoder_outputs = Dense(num_decoder_tokens, activation='softmax')(decoder_lstm_layer)

# Define the model that will turn
# `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
model = Model([encoder_inputs, decoder_inputs], decoder_outputs)

# Compile & run training
model.compile(optimizer='rmsprop', loss='categorical_crossentropy')
# Note that `decoder_target_data` needs to be one-hot encoded,
# rather than sequences of integers like `decoder_input_data`!


labels = np.expand_dims(np.vstack(labels.values), 1)

model.fit([padded_docs, labels], labels,
         epochs=epochs,
         validation_split=0.2)