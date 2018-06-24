from distutils.core import setup
setup(name='rosbag_pandas',
        version='0.5.0.0',
        author = 'Adam Taylor',
        author_email = 'aktaylor08@gmail.com',
        description='Create a Python pandas data frame from a ros bag file',
        py_modules=['rosbag_pandas'],
        scripts=['scripts/bag_graph.py', 'scripts/bag2csv.py'],
        keywords = ['ROS', 'rosbag', 'pandas'],
	url='https://github.com/aktaylor08/RosbagPandas',
        )

