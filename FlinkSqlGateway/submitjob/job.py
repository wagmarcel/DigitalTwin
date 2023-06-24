from pyflink.common import Row, Configuration
from pyflink.table import AggregateFunction, DataTypes, TableEnvironment, EnvironmentSettings
from pyflink.table.expressions import call
from pyflink.table.udf import udaf
from pyflink.table.expressions import col, lit
from pyflink.table.window import Tumble
import json
import pathlib
import os
#import udf.weightedAvg as WeightedAvg


JARDIR = '/opt/gateway/jars'
# Add udf modules

#print(os.getcwd())
#print(os.listdir())
with open('data/SQL-structures.json') as f:
    d = json.load(f)

    # Register udf models

    #config = Configuration()
    #config.set_string('pipeline.name', 'pipelinename')
    env_settings = EnvironmentSettings.in_streaming_mode() #.new_instance().with_configuration(config).build()
    table_env = TableEnvironment.create(env_settings)


    # Get all jars from /opt/gateway/jar
    jars = ';'.join(list(map(lambda x: "file://"+str(x), pathlib.Path(JARDIR).glob('*.jar'))))
    print(jars)

    table_env.get_config().set("pipeline.classpaths", jars)

    # the result type and accumulator type can also be specified in the udaf decorator:
    # weighted_avg = udaf(WeightedAvg(), result_type=DataTypes.BIGINT(), accumulator_type=...)
    #weighted_avg = udaf(udf.weightedAvg.WeightedAvg())
    #table_env.create_temporary_function("weighted_avg", udf.weightedAvg.WeightedAvg())
    #WeightedAvg.register(table_env)
    for file in os.scandir('udf'):
        if file.name.endswith('.py') and file.name != '__init__.py':
            name = file.name[:-3]      # without the '.py' at the end
            package = __import__('udf.' + name)
            #package.register(table_env)
            mod = getattr(package, name)
            mod.register(table_env)

    # Create SETs
    sets = d['sqlsets']
    for set in sets:
            v = set.replace('=', ' ').split(' ')
            key = v[1]
            value = v[-1].strip(';').strip('\'')
            print(f'SET: {key}={value}')
            table_env.get_config().set(key, value)
            #table_env.get_config().set("pipeline.name", "pipelinename")

    # Create Tables
    tables = d['tables']
    for table in tables:
        table_env.execute_sql(table)

    # Create Views
    views = d['views']
    for view in views:
        table_env.execute_sql(view)

    # CREATE SQL Statement SET
    statement_set = table_env.create_statement_set()
    for statement in d["sqlstatementset"]:
        statement_set.add_insert_sql(statement)
        
    statement_set.execute()

    #t = table_env.from_elements([(1, 2, "Lee"),
    #                            (3, 4, "Jay"),
    #                            (5, 6, "Jay"),
    #                            (7, 8, "Lee")]).alias("value", "count", "name")

    #table_env.execute_sql("INSERT into testtable VALUES(1,2, 'Lee');").wait()
    #table_env.create_temporary_view("source", t)

    # call registered function in SQL
    #table_env.execute_sql(
    #    "INSERT INTO aggtable SELECT weighted_avg(`value`, `count`) AS `avg`, `name` FROM testtable GROUP BY name;")