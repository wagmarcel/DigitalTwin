import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
import flink_statetime


class Statetime:
    """ Maximum value in a range of cells. """
    
    def __init__(self):
        try:
            self.accum = [None, None, None]
            self.flink_statetime = flink_statetime.Statetime()
        except Exception as err:
            print(f"Statetime init: {err}")
    def step(self, state, timesInMs):
        try:
            self.flink_statetime.accumulate(self.accum, state, timesInMs)
        except Exception as err:
            print(f"Statetime step: {err}")
    def finalize(self):
        return self.flink_statetime.get_value(self.accum)
                            
