import os
import rosbag_pandas


def test_numbers_3_4():
    df = rosbag_pandas.bag_to_dataframe('data/rosout.bag')
    assert set(df) == {
        'rosout__file', 'rosout__function', 'rosout__level', 'rosout__line',
        'rosout__msg', 'rosout__name'
    }
