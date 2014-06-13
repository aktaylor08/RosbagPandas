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
