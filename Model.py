from keras import Input, Model
from keras.layers import Embedding, LSTM, Dense, Dropout
from keras.optimizers import RMSprop
from numpy import asarray, zeros


def get_model(num_encoder_tokens, num_decoder_tokens, tokenizer, glove_embedding_file,
              encoder_input_data, decoder_input_data):
    BATCH_SIZE = 1
    EPOCHS = 2
    LATENT_DIM = 100

    # GLOVE EMBEDDING

    # load the whole embedding into memory
    embeddings_index = dict()
    f = open(glove_embedding_file)
    for line in f:
        values = line.split()
        word = values[0]
        coefs = asarray(values[1:], dtype='float32')
        embeddings_index[word] = coefs
    f.close()
    print('Loaded %s word vectors.' % len(embeddings_index))

    # create a weight matrix for words in training docs
    embedding_matrix = zeros((num_encoder_tokens, LATENT_DIM))
    for word, i in tokenizer.word_index.items():
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector

    # TRAINING MODEL

    # ENCODER MODEL
    # Define an input sequence and process it.
    encoder_inputs = Input(shape=(None,))
    encoder_embedding_layer = Embedding(num_encoder_tokens, LATENT_DIM, weights=[embedding_matrix], trainable=False)(
        encoder_inputs)
    encoder_lstm_layer, state_h, state_c = LSTM(num_decoder_tokens, return_state=True)(encoder_embedding_layer)
    encoder_states = [state_h, state_c]

    # DECODER MODEL

    # Set up the decoder, using `encoder_states` as initial state.
    decoder_inputs = Input(shape=(None, num_decoder_tokens))
    decoder_lstm_layer = LSTM(num_decoder_tokens, return_sequences=True)(decoder_inputs, initial_state=encoder_states)
    # decoder_dense_hidden_layer = Dense(num_decoder_tokens, activation='relu')(decoder_lstm_layer)
    # decoder_dropout_layer = Dropout(0.5)(decoder_dense_hidden_layer)
    decoder_dense = Dense(num_decoder_tokens, activation='sigmoid')
    decoder_outputs = decoder_dense(decoder_lstm_layer)

    # MODEL COMPILATION

    # Define the model that will turn
    # `encoder_input_data` & `decoder_input_data` into `decoder_target_data`
    model = Model([encoder_inputs, decoder_inputs], decoder_outputs)

    # Compile & run training
    model.compile(loss='mean_squared_error', optimizer="adam", metrics=['accuracy'])
    # model.compile(loss='mean_squared_error', optimizer=RMSprop(lr=0.0001), metrics=['accuracy'])
    # Note that `decoder_target_data` needs to be one-hot encoded,
    # rather than sequences of integers like `decoder_input_data`!

    decoder_input_data_zeros = zeros((787, 1, num_decoder_tokens))

    model.fit([encoder_input_data, decoder_input_data_zeros], decoder_input_data,
              batch_size=BATCH_SIZE, epochs=EPOCHS, validation_split=0.2)

    # INFERENCE MODEL

    # Encoder
    encoder_model = Model(encoder_inputs, encoder_states)

    # Decoder
    decoder_state_input_h = Input(shape=(num_decoder_tokens,))
    decoder_state_input_c = Input(shape=(num_decoder_tokens,))
    decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
    decoder_lstm = LSTM(num_decoder_tokens, return_sequences=True, return_state=True)
    decoder_outputs, state_h, state_c = decoder_lstm(decoder_inputs, initial_state=decoder_states_inputs)
    decoder_states = [state_h, state_c]
    decoder_outputs = Dense(num_decoder_tokens, activation='sigmoid')(decoder_outputs)
    decoder_model = Model(
        [decoder_inputs] + decoder_states_inputs,
        [decoder_outputs] + decoder_states)

    return model, encoder_model, decoder_model
