from pyflink.common import Row
from pyflink.table import AggregateFunction, DataTypes
from pyflink.table.udf import udaf
from enum import IntEnum


class Index(IntEnum):
    """SQL Job states as defined by Flink"""
    STATETIME = 0
    LAST_STATE = 1
    LAST_TIME = 2
    FIRST_STATE = 3
    FIRST_TIME = 4
    BUFFER_ACCUM = 5
    BUFFER_RETRACT = 6


class Last_Aggregator(AggregateFunction):

    def create_accumulator(self):
        # 0: current value 1: next value
        return Row(None, None)

    def get_value(self, accumulator):
        return accumulator[1]

    def accumulate(self, accumulator, value):
        if value is None:
            return
        if accumulator[0] is None:
            accumulator[0] = value
            accumulator[1] = value
        else:
            if value != accumulator[0]:
                accumulator[0] = value
                accumulator[1] = value
            else:
                accumulator[1] = None

    def get_result_type(self):
        return DataTypes.STRING()

    def get_accumulator_type(self):
        return DataTypes.ROW([
                             DataTypes.FIELD("f0", DataTypes.STRING())])


def register(table_env):
    last_aggregator = udaf(Last_Aggregator())
    table_env.create_temporary_function("last_agg", last_aggregator)
