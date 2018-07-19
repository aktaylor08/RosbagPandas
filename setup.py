from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['rosbag_pandas'],
    scripts=['scripts/bag_graph.py', 'scripts/bag2csv.py'],
    package_dir={'': 'src'},
    keywords = ['ROS', 'rosbag', 'pandas'],
)

setup(**d)