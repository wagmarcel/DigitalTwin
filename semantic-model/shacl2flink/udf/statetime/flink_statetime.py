try:
    from pyflink.common import Row
    from pyflink.table import AggregateFunction
    from pyflink.table.expressions import call
    from pyflink.table.udf import udaf
    from pyflink.table.expressions import col, lit
except ImportError:
    class Row():
        def __init__(self, a, b, c, d, e):
            pass
    class AggregateFunction():
        pass


class Statetime(AggregateFunction):

    def create_accumulator(self):
        # statetime, last_state, last_timeInMs, first_state, first_timeInMs
        return Row(None, None, None, None, None)
        pass

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


    def retract(self, accumulator, state, timeInMs):
        if accumulator[3] is None:
            accumulator[4] = timeInMs
            accumulator[3] = state
        else:
            if accumulator[3] == 1:
                accumulator[0] -= (timeInMs - accumulator[4])
            accumulator[4] = timeInMs
            accumulator[3] = state
            
    def get_result_type(self):
        return 'BIGINT'
        
    def get_accumulator_type(self):
        return 'ROW<f0 INT, f1 BIGINT>'