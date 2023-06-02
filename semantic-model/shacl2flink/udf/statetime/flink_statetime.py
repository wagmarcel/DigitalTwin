from pyflink.common import Row
from pyflink.table import AggregateFunction, DataTypes, TableEnvironment, EnvironmentSettings
from pyflink.table.expressions import call
from pyflink.table.udf import udaf
from pyflink.table.expressions import col, lit
from pyflink.table.window import Tumble


class Statetime(AggregateFunction):

    def create_accumulator(self):
        # statetime, last_state, last_timeInMs
        return Row(None, None, None)

    def get_value(self, accumulator):
            return accumulator[0]

    def accumulate(self, accumulator, state, timeInMs):
        if accumulator[1] is None or accumulator[2] is None:
            accumulator[1] = state
            accumulator[2] = timeInMs
        else:
            if accumulator[1] == 1:
                if accumulator[0] is None:
                    accumulator[0] = timeInMs - accumulator[2]
                else:
                    accumulator[0] += timeInMs - accumulator[2]
            accumulator[1] = state
            accumulator[2] = timeInMs
        
    def get_result_type(self):
        return 'BIGINT'
        
    def get_accumulator_type(self):
        return 'ROW<f0 INT, f1 BIGINT>'