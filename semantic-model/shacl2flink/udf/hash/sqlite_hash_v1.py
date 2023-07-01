import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
import flink_hash_v1 as flink_hash


class Hash:
    
    def __init__(self):
        try:
            self.flink_hash = flink_hash.HashCode()
        except Exception as err:
            print(f"Hash init: {err}")


    def eval(self,value):
        try:
            return self.flink_hash.eval(value)
        except Exception as err:
            print(f"Statetime finalize: {err}")
