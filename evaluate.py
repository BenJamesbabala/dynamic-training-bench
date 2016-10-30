#Copyright (C) 2016 Paolo Galeone <nessuno@nerdz.eu>
# Based on Tensorflow cifar10_train.py file
# https://github.com/tensorflow/tensorflow/blob/r0.11/tensorflow/models/image/cifar10/cifar10_train.py
#
#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, you can obtain one at http://mozilla.org/MPL/2.0/.
#Exhibit B is not attached; this software is compatible with the
#licenses expressed under Section 1.12 of the MPL v2.
""" Evaluate the model """

import argparse
import importlib
from datetime import datetime
import math

import numpy as np
import tensorflow as tf


def get_validation_accuracy(checkpoint_dir, model, dataset):
    """
    Read latest saved checkpoint and use it to evaluate the model
    Args:
        checkpoint_dir: checkpoint folder
        model: python package containing the model to save
        dataset: python package containing the dataset to use
    """

    with tf.Graph().as_default(), tf.device('/gpu:1'):
        # Get images and labels from the dataset
        # Use batch_size multiple of train set size and big enough to stay in GPU
        batch_size = 200
        images, labels = dataset.inputs(eval_data=True, batch_size=batch_size)

        # Build a Graph that computes the logits predictions from the
        # inference model.
        _, logits = model.get_model(
            images, DATASET.NUM_CLASSES, train_phase=False)

        # Calculate predictions.
        top_k_op = tf.nn.in_top_k(logits, labels, 1)

        saver = tf.train.Saver()
        accuracy = 0.0
        with tf.Session(config=tf.ConfigProto(
                allow_soft_placement=True)) as sess:
            ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
            if ckpt and ckpt.model_checkpoint_path:
                # Restores from checkpoint
                saver.restore(sess, ckpt.model_checkpoint_path)
            else:
                print('No checkpoint file found')
                return

            # Start the queue runners.
            coord = tf.train.Coordinator()
            try:
                threads = []
                for queue_runner in tf.get_collection(
                        tf.GraphKeys.QUEUE_RUNNERS):
                    threads.extend(
                        queue_runner.create_threads(
                            sess, coord=coord, daemon=True, start=True))

                num_iter = int(
                    math.ceil(dataset.NUM_EXAMPLES_PER_EPOCH_FOR_EVAL /
                              batch_size))
                true_count = 0  # Counts the number of correct predictions.
                total_sample_count = num_iter * batch_size
                step = 0
                while step < num_iter and not coord.should_stop():
                    predictions = sess.run([top_k_op])
                    true_count += np.sum(predictions)
                    step += 1

                accuracy = true_count / total_sample_count
            except Exception as exc:
                coord.request_stop(exc)
            finally:
                coord.request_stop()

            coord.join(threads)
        return accuracy


if __name__ == '__main__':
    # CLI arguments
    PARSER = argparse.ArgumentParser(description="Evaluate the model")
    PARSER.add_argument("--model", required=True)
    PARSER.add_argument("--dataset", required=True)
    PARSER.add_argument("--checkpoint_dir", required=True)
    ARGS = PARSER.parse_args()

    # Load required model and dataset, ovverides default
    MODEL = importlib.import_module("models." + ARGS.model)
    DATASET = importlib.import_module("inputs." + ARGS.dataset)

    DATASET.maybe_download_and_extract()
    print('{}: accuracy = {:.3f}'.format(datetime.now(
    ), get_validation_accuracy(ARGS.checkpoint_dir, MODEL, DATASET)))
