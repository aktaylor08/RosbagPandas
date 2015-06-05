#!/usr/bin/env python
# encoding: utf-8

import rosbag_pandas
import matplotlib.pyplot as plt

import argparse


def buildParser():
    ''' Builds the parser for reading the command line arguments'''
    parser = argparse.ArgumentParser(description='Bagfile reader')
    parser.add_argument('-b', '--bag', help='Bag file to read',
                        required=True, type=str)
    parser.add_argument('-s', '--series',
                        help='Msg data fields to graph',
                        required=True, nargs='*')
    parser.add_argument('-y ', '--ylim',
                        help='Set min and max y lim',
                        required=False, nargs=2)
    parser.add_argument('-c', '--combined',
                        help="Graph them all on one",
                        required=False, action="store_true", dest="sharey")
    return parser


def parse_series_args(topics, fields):
    '''Return which topics and which field keys need to be examined
    for plotting'''
    keys = {}
    for field in fields:
        for topic in topics:
            if field.startswith(topic):
                keys[field] = (topic, field[len(topic) + 1:])

    return keys


def graph(df, df_keys, sharey):
    if sharey or len(df_keys) == 1:
        fig, axes = plt.subplots()
        for label, key in df_keys.items():
            s = df[key].dropna()
            axes.plot(s.index, s.values, label=label)

        axes.legend(loc=0)
        plt.show()
    else:
        fig, axes = plt.subplots(len(df_keys), sharex=True)
        idx = 0
        for label, key in df_keys.items():
            s = df[key].dropna()
            axes[idx].plot(s.index, s.values)
            axes[idx].set_title(label)
            idx = idx + 1
        plt.show()


if __name__ == '__main__':
    ''' Main entry point for the function. Reads the command line arguements
    and performs the requested actions '''
    # Build the command line argument parser
    parser = buildParser()
    # Read the arguments that were passed in
    args = parser.parse_args()
    bag = args.bag
    fields = args.series
    sharey = args.sharey
    yaml_info = rosbag_pandas.get_bag_info(bag)
    topics = rosbag_pandas.get_topics(yaml_info)
    data_keys = parse_series_args(topics, fields)
    df_keys = {}
    topics = []
    for k, v in data_keys.items():
        column = rosbag_pandas.get_key_name(
            v[0]) + '__' + rosbag_pandas.get_key_name(v[1])
        column = column.replace('.', '_')
        df_keys[k] = column
        topics.append(v[0])

    df = rosbag_pandas.bag_to_dataframe(bag, include=topics, seconds=True)
    graph(df, df_keys, sharey)
