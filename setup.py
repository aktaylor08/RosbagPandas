from distutils.core import setup
setup(name='rosbag_pandas',
        version='0.3.1',
        py_modules=['rosbag_pandas'],
        scripts=['scripts/bag_graph.py', 'scripts/bag2csv.py'],
     )
