#!/usr/bin/env python

import argparse
import glob
import os
import rosbag
import roslib; roslib.load_manifest('rosbag')
import subprocess
import types
import yaml

import pandas as pd
import numpy as np

def bag_to_dataframe(bag_name, include='all', exclude=None):
    #get list of topics to parse
    bag_topics = get_topics(bag_name)
    bag_topics = prune_topics(bag_topics, include, exclude)

    bag = rosbag.Bag(bag_name)
    msgs_to_read = get_field_names(bag, bag_topics, False)
    data = create_data_stuct(msgs_to_read)
    dmap, size = create_data_map(msgs_to_read)

    datastore = []
    index = []


    #all of the data is loaded
    for topic, msg, mt in bag.read_messages(topics=bag_topics):
        row = np.empty((size), dtype=object)
        row[:] = np.NaN
        dt = pd.to_datetime(mt.to_nsec())
        index.append(dt)
        fields = dmap[topic]
        for f, idx in fields.items():
            row[idx] = get_message_data(msg, f)
        datastore.append(row)
                
    bag.close()
    col_names = np.empty((size), dtype=object)
    for t in dmap.keys():
        for f, idx in dmap[t].items():
            name = get_key_name(t) + '__' + f 
            name = name.replace('.', '_')
            col_names[idx] = name


    #now we have read all of the messages its time to assemble the dataframe
    return pd.DataFrame(data=datastore, index=index, columns=col_names)
            
def create_data_stuct(msgs_to_read):
    data = {}
    for topic in msgs_to_read.keys():
        fields = {field: [[],[]] for field in msgs_to_read[topic]}
        data[topic] = fields
    return data


def create_data_map(msgs_to_read):
    idx = 0
    dmap = {}
    for topic in msgs_to_read.keys():
        fields = {}
        for f in msgs_to_read[topic]:
            fields[f]  =idx
            idx = idx + 1
        dmap[topic] = fields
    return (dmap, idx)


def prune_topics(bag_topics, include, exclude):
    topics_to_use = set()
    #add all of the topics
    if include == 'all':
        for t in bag_topics:
            topics_to_use.add(t)
    else:
        #add all of the includes if it is in the topic
        for topic in include:
            if topic in bag_topics:
                topics_to_use.add(topic)

    #now exclude the exclusions
    if exclude is not None:
        for remove in exclude:
            if remove in exclude:
                topics_to_use.remove(remove)

    #return a list for the results 
    return list(topics_to_use)


def get_field_names(bag_file, topics, output):
    ''' Reads through a bag file and for a given set of topics, builds
        a dictionary that holds all of the messages associated with each
        topic '''
    msgs = {}

    # Go through every requested topic
    for topic in topics:
        if output:
            print 'Getting messages for topic: ' + topic
        # These are the strings that will allow access to the messages in the
        # topic
        msg_paths = []
        # For each topic, we have a set of messages that are nested arbitrarily
        # deep. For instance, consider a topic /subject_pose/ that is
        # publishing StampedPose messages. We would want to build a dictionary
        # with the topic name as the key, with the following messages in a list
        # associated with that key.
        for _, msg, _ in bag_file.read_messages(topic):
            # For each message in the bag, recursively descend down the nested
            # structure to the get to the raw data types
            msg_paths = get_base_fields(msg,'')         
            # Associate every discovered message with this topic
            msgs[topic] = msg_paths
            if output:
                for path in msg_paths:
                    print '\t' + path
            # I assume that every instance of the topic in the bag will have
            # the same structure, so after we see the first one, break out
            # of this loop
            break

    return msgs


def get_topics(bag_file):
    ''' Returns the names of all of the topics in the bag, and prints them
        to stdout if requested
    '''
    # Get the info on the bag
    bag_info = yaml.load(subprocess.Popen(['rosbag', 'info', '--yaml', \
            bag_file], stdout=subprocess.PIPE).communicate()[0])
    # Pull out the topic info
    topics = bag_info['topics']
    names = []

    # Store all of the topics in a dictionary
    for topic in topics:
        names.append(topic['topic'])

    return names


def get_base_fields(msg, prefix=''):
    '''function to get the full names of every message field in the message'''
    slots = msg.__slots__
    ret_val = []
    for i in slots:
        slot_msg = getattr(msg, i)
        if hasattr(slot_msg, '__slots__'):
                subs = get_base_fields(slot_msg, prefix=prefix + i + '.')
                for i in subs:
                    ret_val.append(i)
        else:
            ret_val.append(prefix + i)
    return ret_val 


def get_message_data(msg, key):
    '''get the datapoint from the dot delimited message field key 
    e.g. translation.x looks up translation than x and returns the value found
    in x'''
    data = msg 
    paths = key.split('.')
    for i in paths:
        data = getattr(data, i)
    return data


def get_key_name(name):
    '''fix up topic to key names to make them a little prettier'''
    if name[0] == '/':
        name = name[1:]
    name = name.replace('/', '.')
    return name



