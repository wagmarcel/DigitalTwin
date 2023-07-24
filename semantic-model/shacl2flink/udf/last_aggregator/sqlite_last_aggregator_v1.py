import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
import flink_last_aggregator_v1 as flink_last_aggregtor  # noqa: E402


class Last_Aggregator:
    """ Maximum value in a range of cells. """

    def __init__(self):
        try:
            self.accum = [None, None]
            self.flink_last_aggregator = flink_last_aggregtor.Last_Aggregator()
        except Exception as err:
            print(f"LA init: {err}")

    def step(self, value):
        try:
            self.flink_last_aggregator.accumulate(self.accum, value)
        except Exception as err:
            print(f"Statetime step: {err}")

    def value(self):
        try:
            return self.flink_last_aggregator.get_value(self.accum)
        except Exception as err:
            print(f"LA value: {err}")

    def finalize(self):
        try:
            return self.flink_last_aggregator.get_value(self.accum)
        except Exception as err:
            print(f"LA finalize: {err}")

    #def inverse(self, state, timesInMs):
    #    try:
    #        self.flink_statetime.retract(self.accum, state, timesInMs)
    #    except Exception as err:
    #        print(f"Statetime inverse: {err}")
