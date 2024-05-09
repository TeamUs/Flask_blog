# rnn.py
from keras.models import Sequential
import numpy as np
import tensorflow as tf

class RNNModel:
    def __init__(self, X_train):
        self.model = Sequential([tf.keras.layers.SimpleRNN(64, input_shape=(X_train.shape[1], 1)),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

    def train(self, X_train, y_train):
        self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        self.model.fit(np.expand_dims(X_train, axis=2), y_train, epochs=20, batch_size=32)

    def predict(self, X_test):
        return self.model.predict(X_test)
