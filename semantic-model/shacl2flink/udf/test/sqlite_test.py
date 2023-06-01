import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
import flink_test


    
class Test:
    """ Maximum value in a range of cells. """
    
    def __init__(self):
        try:
            self.accum = [None]
            self.flink_max = flink_test.Max()
        except Exception as err:
            print(err)
    def step(self, *values):
        try:
            for value in values:
                self.flink_max.accumulate(self.accum, value)
        except Exception as err:
            print(f"xx{err}")
                    
    def finalize(self):
        return self.flink_max.get_value(self.accum)
                            
