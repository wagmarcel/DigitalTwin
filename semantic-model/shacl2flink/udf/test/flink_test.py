from pyflink.common import Row
from pyflink.table import AggregateFunction, DataTypes, TableEnvironment, EnvironmentSettings
from pyflink.table.expressions import call
from pyflink.table.udf import udaf
from pyflink.table.expressions import col, lit
from pyflink.table.window import Tumble


class Max(AggregateFunction):

    def create_accumulator(self):
        return Row(None)

    def get_value(self, accumulator):
            return accumulator[0]

    def accumulate(self, accumulator, value):
        if accumulator[0] is None:
            accumulator[0] = value
        else:
            if accumulator[0] < value:
                accumulator[0] = value 
        
    def get_result_type(self):
        return 'BIGINT'
        
    def get_accumulator_type(self):
        return 'ROW<f0 BIGINT, f1 BIGINT>'