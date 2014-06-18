============
RosbagPandas
============

RosbagPandas provides a quick way to load rosbag files 
into a Pandas Dataframe object for data viewing
and manipulation. Usage is similar to the following:

    #!/usr/bin.env python
    import rosbag_pandas

    dataframe = rosbag_pandas.bag_to_dataframe('file.bag')
    #awesome data processing


In addition to parsing and taking in the whole
bag the function can use the include and exclude
parameters to limit the topics read into the dataframe.

Examples include using a regular expression to filter or add topics
as well as filtering or adding from a list.

Also installs two scripts:

bag_graph.py which allows a user to produce a quick graph of data in a bag file.

bag2csv.py allows a user to quickly convert data in a rosbag into csv format.
