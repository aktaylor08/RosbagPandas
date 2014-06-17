#!/usr/bin/env python

import warnings

import argparse
import glob
import os

import rosbag
import re


import subprocess
import types
import yaml

import pandas as pd
import numpy as np

def bag_to_dataframe(bag_name, include=None, exclude=None):
    #get list of topics to parse
    yaml_info = get_bag_info(bag_name)
    bag_topics = get_topics(yaml_info)
    bag_topics = prune_topics(bag_topics, include, exclude)
    length = get_length(bag_topics, yaml_info)

    bag = rosbag.Bag(bag_name)
    msgs_to_read = get_field_names(bag, bag_topics, False)
    dmap = create_data_map(msgs_to_read)



    #create datastore
    datastore =  {}
    for topic in dmap.keys():
        for f, key in dmap[topic].items():
            arr = np.empty(length)
            arr.fill(np.NAN)
            datastore[key] = arr

    #create the index
    index = np.empty(length) 
    index.fill(np.NAN)


    #all of the data is loaded
    idx = 0
    for topic, msg, mt in bag.read_messages(topics=bag_topics):
        index[idx] = mt.to_nsec()
        fields = dmap[topic]
        for f, key in fields.items():
            try:
                d = get_message_data(msg, f)
                datastore[key][idx] = d 
            except:
                pass
        idx = idx + 1
                
    bag.close()

    #convert the index
    index = pd.to_datetime(index, unit='ns')

    #now we have read all of the messages its time to assemble the dataframe
    return pd.DataFrame(data=datastore, index=index)
            

def get_length(topics, yaml_info):
    total = 0
    info = yaml_info['topics']
    for topic in topics:
        for t in info:
            if t['topic'] == topic:
                total = total + t['messages']
                break
    return total

def create_data_map(msgs_to_read):
    dmap = {}
    for topic in msgs_to_read.keys():
        base_name = get_key_name(topic) + '__'  
        fields = {}
        for f in msgs_to_read[topic]:
            key = (base_name + f).replace('.', '_')
            fields[f]  = key
        dmap[topic] = fields
    return dmap


def prune_topics(bag_topics, include, exclude):
    '''prune the topics.  If include is None add all to the set of topics to use
       if include is a string regex match that string, if it is a list use the 
        list   
        
        If exclude is None do nothing, if string remove the topics with regex,
        if it is a list remove those topics''' 

    topics_to_use = set()
    #add all of the topics
    if include is None:
        for t in bag_topics:
            topics_to_use.add(t)
    elif isinstance(include, basestring):
        check = re.compile(include)
        for t in bag_topics:
            if re.match(check, t) is not None:
                topics_to_use.add(t)
    else:
        try:
        #add all of the includes if it is in the topic
            for topic in include:
                if topic in bag_topics:
                    topics_to_use.add(topic)
        except:
            warnings.warn('Error in topic selection Using All!')
            topics_to_use = set()
            for t in bag_topics:
                topics_to_use.add(t)

    to_remove = set() 
    #now exclude the exclusions
    if exclude is None:
        pass
    elif isinstance(exclude, basestring):
        check = re.compile(exclude)
        for t in list(topics_to_use):
            if re.match(check,t) is not None:
                to_remove.add(t)
    else:
        for remove in exclude:
            if remove in exclude:
                to_remove.add(remove)

    #final set stuff to get topics to use
    topics_to_use = topics_to_use - to_remove
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

def get_bag_info(bag_file):
    '''Get uamle dict of the bag information
    by calling the subprocess -- used to create correct sized
    arrays'''
    # Get the info on the bag
    bag_info = yaml.load(subprocess.Popen(['rosbag', 'info', '--yaml', \
            bag_file], stdout=subprocess.PIPE).communicate()[0])
    return bag_info



def get_topics(yaml_info):
    ''' Returns the names of all of the topics in the bag, and prints them
        to stdout if requested
    '''
    # Pull out the topic info
    names = []
    # Store all of the topics in a dictionary
    topics = yaml_info['topics']
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

if __name__ == '__main__':
    df = bag_to_dataframe('/home/ataylor/data/dat/wind2.bag', include='/a/')
    # print df.columns
    # print df.head(1)



