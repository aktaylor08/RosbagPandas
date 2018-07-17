#!/usr/bin/env python

import warnings
import re
import subprocess
import yaml

import pandas as pd
import numpy as np

import rosbag
from roslib.message import get_message_class


def bag_to_dataframe(bag_name, include=None, exclude=None, parse_header=False, seconds=False):
    '''
    Read in a rosbag file and create a pandas data frame that
    is indexed by the time the message was recorded in the bag.

    :bag_name: String name for the bag file
    :include: None, String, or List  Topics to include in the dataframe
               if None all topics added, if string it is used as regular
                   expression, if list that list is used.
    :exclude: None, String, or List  Topics to be removed from those added
            using the include option using set difference.  If None no topics
            removed. If String it is treated as a regular expression. A list
            removes those in the list.

    :seconds: time index is in seconds

    :returns: a pandas dataframe object
    '''
    # get list of topics to parse
    yaml_info = get_bag_info(bag_name)
    bag_topics = get_topics(yaml_info)
    bag_topics = prune_topics(bag_topics, include, exclude)
    length = get_length(bag_topics, yaml_info)
    msgs_to_read, msg_type = get_msg_info(yaml_info, bag_topics, parse_header)

    bag = rosbag.Bag(bag_name)
    dmap = create_data_map(msgs_to_read)

    # create datastore
    datastore = {}
    for topic in dmap.keys():
        for f, key in dmap[topic].iteritems():
            t = msg_type[topic][f]
            if isinstance(t, int) or isinstance(t, float):
                arr = np.empty(length)
                arr.fill(np.NAN)
            elif isinstance(t, list):
                arr = np.empty(length)
                arr.fill(np.NAN)
                for i in range(len(t)):
                    key_i = '{0}{1}'.format(key, i)
                    datastore[key_i] = arr.copy()
                continue
            else:
                arr = np.empty(length, dtype=np.object)
            datastore[key] = arr

    # create the index
    index = np.empty(length)
    index.fill(np.NAN)

    # all of the data is loaded
    for idx, (topic, msg, mt) in enumerate(bag.read_messages(topics=bag_topics)):
        try:
            if seconds:
                index[idx] = msg.header.stamp.to_sec()
            else:
                index[idx] = msg.header.stamp.to_nsec()
        except:
            if seconds:
                index[idx] = mt.to_sec()
            else:
                index[idx] = mt.to_nsec()
        fields = dmap[topic]
        for f, key in fields.iteritems():
            try:
                d = get_message_data(msg, f)
                if isinstance(d, tuple):
                    for i, val in enumerate(d):
                        key_i = '{0}{1}'.format(key, i)
                        datastore[key_i][idx] = val
                else:
                    datastore[key][idx] = d
            except:
                pass

    bag.close()

    # convert the index
    if not seconds:
        index = pd.to_datetime(index, unit='ns')

    # now we have read all of the messages its time to assemble the dataframe
    return pd.DataFrame(data=datastore, index=index)


def get_length(topics, yaml_info):
    '''
    Find the length (# of rows) in the created dataframe
    '''
    total = 0
    info = yaml_info['topics']
    for topic in topics:
        for t in info:
            if t['topic'] == topic:
                total = total + t['messages']
                break
    return total


def create_data_map(msgs_to_read):
    '''
    Create a data map for usage when parsing the bag
    '''
    dmap = {}
    for topic in msgs_to_read.keys():
        base_name = get_key_name(topic) + '__'
        fields = {}
        for f in msgs_to_read[topic]:
            key = (base_name + f).replace('.', '_')
            fields[f] = key
        dmap[topic] = fields
    return dmap


def prune_topics(bag_topics, include, exclude):
    '''prune the topics.  If include is None add all to the set of topics to
       use if include is a string regex match that string,
       if it is a list use the list

        If exclude is None do nothing, if string remove the topics with regex,
        if it is a list remove those topics'''

    topics_to_use = set()
    # add all of the topics
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
            # add all of the includes if it is in the topic
            for topic in include:
                if topic in bag_topics:
                    topics_to_use.add(topic)
        except:
            warnings.warn('Error in topic selection Using All!')
            topics_to_use = set()
            for t in bag_topics:
                topics_to_use.add(t)

    to_remove = set()
    # now exclude the exclusions
    if exclude is None:
        pass
    elif isinstance(exclude, basestring):
        check = re.compile(exclude)
        for t in list(topics_to_use):
            if re.match(check, t) is not None:
                to_remove.add(t)
    else:
        for remove in exclude:
            if remove in exclude:
                to_remove.add(remove)

    # final set stuff to get topics to use
    topics_to_use = topics_to_use - to_remove
    # return a list for the results
    return list(topics_to_use)


def get_msg_info(yaml_info, topics, parse_header=True):
    '''
    Get info from all of the messages about what they contain
    and will be added to the dataframe
    '''
    topic_info = yaml_info['topics']
    msgs = {}
    classes = {}

    for topic in topics:
        base_key = get_key_name(topic)
        msg_paths = []
        msg_types = {}
        for info in topic_info:
            if info['topic'] == topic:
                msg_class = get_message_class(info['type'])
                if msg_class is None:
                    warnings.warn(
                        'Could not find types for ' + topic + ' skpping ')
                else:
                    (msg_paths, msg_types) = get_base_fields(msg_class(), "",
                                                             parse_header)
                msgs[topic] = msg_paths
                classes[topic] = msg_types
    return (msgs, classes)


def get_bag_info(bag_file):
    '''Get uamle dict of the bag information
    by calling the subprocess -- used to create correct sized
    arrays'''
    # Get the info on the bag
    bag_info = yaml.load(subprocess.Popen(
        ['rosbag', 'info', '--yaml', bag_file],
        stdout=subprocess.PIPE).communicate()[0])
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


def get_base_fields(msg, prefix='', parse_header=True):
    '''function to get the full names of every message field in the message'''
    slots = msg.__slots__
    ret_val = []
    msg_types = dict()
    for i in slots:
        slot_msg = getattr(msg, i)
        if not parse_header and i == 'header':
            continue
        if hasattr(slot_msg, '__slots__'):
                (subs, type_map) = get_base_fields(
                    slot_msg, prefix=prefix + i + '.',
                    parse_header=parse_header,
                )

                for i in subs:
                    ret_val.append(i)
                for k, v in type_map.items():
                    msg_types[k] = v
        else:
            ret_val.append(prefix + i)
            msg_types[prefix + i] = slot_msg
    return (ret_val, msg_types)


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


def clean_for_export(df):
    new_df = pd.DataFrame()
    for c, t in df.dtypes.iteritems():
        if t.kind in 'OSUV':
            s = df[c].dropna().apply(func=str)
            s = s.str.replace('\n', '')
            s = s.str.replace('\r', '')
            s = s.str.replace(',','\t')
            new_df[c] = s
        else:
            new_df[c] = df[c]

    return new_df
