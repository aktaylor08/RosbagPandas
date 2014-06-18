from distutils.core import setup
setup(name='rosbag_pandas',
        version='0.3.2',
        description='Create a Python pandas data frame from a ros bag file',
        py_modules=['rosbag_pandas'],
        scripts=['scripts/bag_graph.py', 'scripts/bag2csv.py'],
     )
