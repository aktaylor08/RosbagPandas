#!/usr/bin/env python
# encoding: utf-8

import rosbag_pandas
import matplotlib.pyplot as plt

import os

import argparse


def buildParser():
    ''' Builds the parser for reading the command line arguments'''
    parser = argparse.ArgumentParser(
        description='Script to parse bagfile to csv file')
    parser.add_argument('bag', help='Bag file to read',
                        type=str)
    parser.add_argument('-i', '--include',
                        help='list or regex for topics to include',
                        nargs='*')
    parser.add_argument('-e', '--exclude',
                        help='list or regex for topics to exclude',
                        nargs='*')
    parser.add_argument('-o', '--output',
                        help='name of the output file',
                        nargs='*')
    parser.add_argument('-f', '--fill',
                        help='Fill the bag forward and backwards so no missing values when present',
                        action='store_true')
    parser.add_argument('--include-header',
                        help='Include the header fields.  By default they are excluded',
                        action='store_true')
    return parser


def do_work(bag, include, exclude, output, fill, header):
    # covert a lenght one value to a regex
    if include is not None and len(include) == 1:
        include = include[0]

    # covert a lenght one value to a regex
    if exclude is not None and len(exclude) == 1:
        exclude = exclude[0]
    df = rosbag_pandas.bag_to_dataframe(bag, include=include, exclude=exclude, 
            parse_header=header)
    if fill:
        df = df.ffill().bfill()

    if output is None:
        base, _ = os.path.splitext(bag)
        output = base + '.csv'
    df = rosbag_pandas.clean_for_export(df)
    df.to_csv(output)


if __name__ == '__main__':
    ''' Main entry point for the function. Reads the command line arguements
    and performs the requested actions '''
    # Build the command line argument parser
    parser = buildParser()
    # Read the arguments that were passed in
    args = parser.parse_args()
    bag = args.bag
    include = args.include
    exclude = args.exclude
    output = args.output
    fill = args.fill
    header = args.include_header

    do_work(bag, include, exclude, output, fill, header)
