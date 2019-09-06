from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import errno
import collections
import json
import math

import numpy as np
import tensorflow as tf
import pyhocon

def make_summary(value_dict):
  return tf.Summary(value=[tf.Summary.Value(tag=k, simple_value=v) for k,v in value_dict.items()])

def flatten(l):
  return [item for sublist in l for item in sublist]

def get_config(filename):
  return pyhocon.ConfigFactory.parse_file(filename)

def print_config(config):
  print(pyhocon.HOCONConverter.convert(config, "hocon"))

def set_gpus(*gpus):
  os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(str(g) for g in gpus)
  print("Setting CUDA_VISIBLE_DEVICES to: {}".format(os.environ["CUDA_VISIBLE_DEVICES"]))

def mkdirs(path):
  try:
    os.makedirs(path)
  except OSError as exception:
    if exception.errno != errno.EEXIST:
      raise
  return path

def load_char_dict(char_vocab_path):
  vocab = [u"<unk>"]
  with open(char_vocab_path) as f:
    vocab.extend(unicode(c, "utf-8").strip() for c in f.readlines())
  char_dict = collections.defaultdict(int)
  char_dict.update({c:i for i,c in enumerate(vocab)})
  return char_dict

def maybe_divide(x, y):
  return 0 if y == 0 else x / float(y)

def projection(inputs, output_size, initializer=None):
  return ffnn(inputs, 0, -1, output_size, dropout=None, output_weights_initializer=initializer)

def shape(x, dim):
  return x.get_shape()[dim].value or tf.shape(x)[dim]

def ffnn(inputs, num_hidden_layers, hidden_size, output_size, dropout, output_weights_initializer=None):
  if len(inputs.get_shape()) > 2:
    current_inputs = tf.reshape(inputs, [-1, shape(inputs, -1)])
  else:
    current_inputs = inputs

  for i in xrange(num_hidden_layers):
    hidden_weights = tf.get_variable("hidden_weights_{}".format(i), [shape(current_inputs, 1), hidden_size])
    hidden_bias = tf.get_variable("hidden_bias_{}".format(i), [hidden_size])
    current_outputs = tf.nn.relu(tf.nn.xw_plus_b(current_inputs, hidden_weights, hidden_bias))

    if dropout is not None:
      current_outputs = tf.nn.dropout(current_outputs, dropout)
    current_inputs = current_outputs

  output_weights = tf.get_variable("output_weights", [shape(current_inputs, 1), output_size], initializer=output_weights_initializer)
  output_bias = tf.get_variable("output_bias", [output_size])
  outputs = tf.nn.xw_plus_b(current_inputs, output_weights, output_bias)

  if len(inputs.get_shape()) == 3:
    outputs = tf.reshape(outputs, [shape(inputs, 0), shape(inputs, 1), output_size])
  elif len(inputs.get_shape()) > 3:
    raise ValueError("FFNN with rank {} not supported".format(len(inputs.get_shape())))
  return outputs

def cnn(inputs, filter_sizes, num_filters):
  num_words = shape(inputs, 0)
  num_chars = shape(inputs, 1)
  input_size = shape(inputs, 2)
  outputs = []
  for i, filter_size in enumerate(filter_sizes):
    with tf.variable_scope("conv_{}".format(i)):
      w = tf.get_variable("w", [filter_size, input_size, num_filters])
      b = tf.get_variable("b", [num_filters])
    conv = tf.nn.conv1d(inputs, w, stride=1, padding="VALID") # [num_words, num_chars - filter_size, num_filters]
    h = tf.nn.relu(tf.nn.bias_add(conv, b)) # [num_words, num_chars - filter_size, num_filters]
    pooled = tf.reduce_max(h, 1) # [num_words, num_filters]
    outputs.append(pooled)
  return tf.concat(outputs, 1) # [num_words, num_filters * len(filter_sizes)]

def get_timing_signal_1d(length, channels, min_timescale=1.0, max_timescale=1.0e4):
  position = tf.to_float(tf.range(length))
  num_timescales = channels // 2
  log_timescale_increment = (
      math.log(float(max_timescale) / float(min_timescale)) /
      (tf.to_float(num_timescales) - 1))
  inv_timescales = min_timescale * tf.exp(
      tf.to_float(tf.range(num_timescales)) * -log_timescale_increment)
  scaled_time = tf.expand_dims(position, 1) * tf.expand_dims(inv_timescales, 0)
  signal = tf.concat([tf.sin(scaled_time), tf.cos(scaled_time)], axis=1)
  signal = tf.pad(signal, [[0, 0], [0, tf.mod(channels, 2)]])
  signal = tf.reshape(signal, [1, length, channels])
  return signal


def add_timing_signal_1d(x, min_timescale=1.0, max_timescale=1.0e4):
  length = tf.shape(x)[1]
  channels = tf.shape(x)[2]
  signal = get_timing_signal_1d(length, channels, min_timescale, max_timescale)
  return x + signal


def add_timing_signal_1d_given_position(x, position, min_timescale=1.0, max_timescale=1.0e4):
  channels = tf.shape(x)[2]
  num_timescales = channels // 2
  log_timescale_increment = (
      math.log(float(max_timescale) / float(min_timescale)) /
      (tf.to_float(num_timescales) - 1))
  inv_timescales = min_timescale * tf.exp(
      tf.to_float(tf.range(num_timescales)) * -log_timescale_increment)
  scaled_time = (tf.expand_dims(tf.to_float(position), 2) *
                 tf.expand_dims(tf.expand_dims(inv_timescales, 0), 0))
  signal = tf.concat([tf.sin(scaled_time), tf.cos(scaled_time)], axis=2)
  signal = tf.pad(signal, [[0, 0], [0, 0], [0, tf.mod(channels, 2)]])
  return x + signal

def batch_gather(emb, indices):
  batch_size = shape(emb, 0)
  seqlen = shape(emb, 1)
  flattened_emb = tf.reshape(emb, [batch_size * seqlen, -1])  # [batch_size * seqlen, emb]
  offset = tf.expand_dims(tf.range(batch_size) * seqlen, 1)  # [batch_size, 1]
  return tf.gather(flattened_emb, indices + offset) # [batch_size, num_indices, emb]

class RetrievalEvaluator(object):
  def __init__(self):
    self._num_correct = 0
    self._num_gold = 0
    self._num_predicted = 0

  def update(self, gold_set, predicted_set):
    self._num_correct += len(gold_set & predicted_set)
    self._num_gold += len(gold_set)
    self._num_predicted += len(predicted_set)

  def recall(self):
    return maybe_divide(self._num_correct, self._num_gold)

  def precision(self):
    return maybe_divide(self._num_correct, self._num_predicted)

  def metrics(self):
    recall = self.recall()
    precision = self.precision()
    f1 = maybe_divide(2 * recall * precision, precision + recall)
    return recall, precision, f1

class EmbeddingDictionary(object):
  def __init__(self, info, normalize=True, maybe_cache=None):
    self._size = info["size"]
    self._lowercase = info["lowercase"]
    self._normalize = normalize
    self._path = info["path"]
    if maybe_cache is not None and maybe_cache._path == self._path:
      assert self._size == maybe_cache._size
      assert self._lowercase == maybe_cache._lowercase
      self._embeddings = maybe_cache._embeddings
    else:
      self._embeddings = self.load_embedding_dict(self._path, info["format"])

  @property
  def size(self):
    return self._size

  def load_embedding_dict(self, path, file_format):
    print("Loading word embeddings from {}...".format(path))
    default_embedding = np.zeros(self.size)
    embedding_dict = collections.defaultdict(lambda:default_embedding)
    if len(path) > 0:
      is_vec = (file_format == "vec")
      vocab_size = None
      with open(path, "r") as f:
        #for i, line in enumerate(f.readlines()):
        i = 0
        for line in f:
          splits = line.split()
          if i == 0 and is_vec:
            vocab_size = int(splits[0])
            assert int(splits[1]) == self.size
          else:
            #if len(splits) != self.size + 1: continue
            assert len(splits) == self.size + 1
            word = splits[0]
            embedding = np.array([float(s) for s in splits[1:]])
            embedding_dict[word] = embedding
          i += 1
        f.close()
      if vocab_size is not None:
        assert vocab_size == len(embedding_dict)
      print("Done loading word embeddings.")
    return embedding_dict

  def __getitem__(self, key):
    if self._lowercase:
      key = key.lower()
    embedding = self._embeddings[key]
    if self._normalize:
      embedding = self.normalize(embedding)
    return embedding

  def normalize(self, v):
    norm = np.linalg.norm(v)
    if norm > 0:
      return v / norm
    else:
      return v

class CustomLSTMCell(tf.contrib.rnn.RNNCell):
  def __init__(self, num_units, batch_size, dropout):
    self._num_units = num_units
    self._dropout = dropout
    self._dropout_mask = tf.nn.dropout(tf.ones([batch_size, self.output_size]), dropout)
    self._initializer = self._block_orthonormal_initializer([self.output_size] * 3)
    initial_cell_state = tf.get_variable("lstm_initial_cell_state", [1, self.output_size])
    initial_hidden_state = tf.get_variable("lstm_initial_hidden_state", [1, self.output_size])
    self._initial_state = tf.contrib.rnn.LSTMStateTuple(initial_cell_state, initial_hidden_state)

  @property
  def state_size(self):
    return tf.contrib.rnn.LSTMStateTuple(self.output_size, self.output_size)

  @property
  def output_size(self):
    return self._num_units

  @property
  def initial_state(self):
    return self._initial_state

  def __call__(self, inputs, state, scope=None):
    """Long short-term memory cell (LSTM)."""
    with tf.variable_scope(scope or type(self).__name__):  # "CustomLSTMCell"
      c, h = state
      h *= self._dropout_mask
      concat = projection(tf.concat([inputs, h], 1), 3 * self.output_size, initializer=self._initializer)
      i, j, o = tf.split(concat, num_or_size_splits=3, axis=1)
      i = tf.sigmoid(i)
      new_c = (1 - i) * c  + i * tf.tanh(j)
      new_h = tf.tanh(new_c) * tf.sigmoid(o)
      new_state = tf.contrib.rnn.LSTMStateTuple(new_c, new_h)
      return new_h, new_state

  def _orthonormal_initializer(self, scale=1.0):
    def _initializer(shape, dtype=tf.float32, partition_info=None):
      M1 = np.random.randn(shape[0], shape[0]).astype(np.float32)
      M2 = np.random.randn(shape[1], shape[1]).astype(np.float32)
      Q1, R1 = np.linalg.qr(M1)
      Q2, R2 = np.linalg.qr(M2)
      Q1 = Q1 * np.sign(np.diag(R1))
      Q2 = Q2 * np.sign(np.diag(R2))
      n_min = min(shape[0], shape[1])
      params = np.dot(Q1[:, :n_min], Q2[:n_min, :]) * scale
      return params
    return _initializer

  def _block_orthonormal_initializer(self, output_sizes):
    def _initializer(shape, dtype=np.float32, partition_info=None):
      assert len(shape) == 2
      assert sum(output_sizes) == shape[1]
      initializer = self._orthonormal_initializer()
      params = np.concatenate([initializer([shape[0], o], dtype, partition_info) for o in output_sizes], 1)
      return params
    return _initializer
