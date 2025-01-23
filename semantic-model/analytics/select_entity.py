import psycopg2
from psycopg2.extras import DictCursor
from string import Template
import time

# Database connection details
db_config = {
    "dbname": "tsdb",
    "user": "ngb",
    "password": "5t2Aop2p9Uo12Ewq5HvQZcsH2mn5Skuk",
    "host": "acid-cluster",  # or the IP of your PostgreSQL server
    "port": 5432          # default PostgreSQL port
}

id = 'urn:plasmacutter-test:1234567'
targetDate = '2025-01-22 10:44:26'

# SQL query
sql_query_attributes_temp = '''
SELECT *
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY "id" ORDER BY "observedAt" DESC) AS row_num
  FROM attributes AS A
  WHERE "entityId" = '${entityId}'
    AND "observedAt" < '${targetDate}'
) subquery
WHERE row_num = 1;
'''

sql_query_entities_temp = '''
SELECT *
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY "id" ORDER BY "observedAt" DESC) AS row_num
  FROM entities AS A
  WHERE "id" = '${id}'
    AND "observedAt" < '${targetDate}'
) subquery
WHERE row_num = 1;
'''

sql_query_attributes = Template(sql_query_attributes_temp)
sql_query_entities = Template(sql_query_entities_temp)

def convertSQLDateTimeToTimestamp(value):
    return value.strftime('%Y-%m-%dT%H:%M:%S.%f')

def build_ngsild_from_sql(entity_row, attribute_rows):
    parentIds = {}
    def add_attribute(obj, row):
        attribute_id = row['attributeId']
        if attribute_id not in obj: 
            obj[attribute_id] = []
        attribute = {}
        attribute['type'] = row.get('attributeType')
        attribute['datasetId'] = row.get('datasetId')
        node_type = row.get('nodeType')
        if node_type == '@value':
            attribute['value'] = row.get('value')
        else:
            if row.get('attributeType').endswith('Property'):
                attribute['value'] = {
                    '@id': row.get('value')
                }
            elif row.get('attributeType').endswith('Relationship'):
                attribute['object'] = row.get('value')
        attribute['observedAt'] = convertSQLDateTimeToTimestamp(row.get('observedAt'))
        attribute['modifiedAt'] = convertSQLDateTimeToTimestamp(row.get('modifiedAt'))
        
        if row['id'] in parentIds:
            # children = []
            for r in parentIds[row['id']]:
                # child_attribute_id = r['attributeId']
                add_attribute( attribute, r)

        obj[attribute_id].append(attribute)
   
    ngsild_object = {}
    erow = dict(entity_row[0])
    ngsild_object['id'] = erow['id']
    ngsild_object['type'] = erow['type']
    # First cache parentIds
    for row in attribute_rows:
        arow = dict(row)
        parentId = arow['parentId']
        if parentId is not None:
            if parentId not in parentIds:
                parentIds[parentId] = []
            datasetId = arow.get('datasetId')
            parentIds[parentId].append(arow)
    # Now process attributes recursively
    for row in attribute_rows:
        arow = dict(row)
        parentId = arow.get('parentId')
        if parentId is None:
            add_attribute(ngsild_object, arow)
        
    
    print(ngsild_object)


try:
    # Connect to the database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # Read SQL commands from the file
    #with open(sql_file_path, "r") as file:
    #    sql_commands = file.read()
    
    # Execute the SQL commands
    cursor.execute(sql_query_attributes.substitute(entityId=id, targetDate=targetDate))
    attribute_rows = cursor.fetchall()
    
    cursor.execute(sql_query_entities.substitute(id=id, targetDate=targetDate))
    entity_row = cursor.fetchall()
    
    # List all retrieved rows
    for row in attribute_rows:
        print(dict(row))
    # Commit changes (if needed)
    conn.commit()
    print("SQL script executed successfully.")
    build_ngsild_from_sql(entity_row, attribute_rows)
    

except Exception as e:
    raise e
    print(f"Error: {e}")
    if conn:
        conn.rollback()  # Roll back in case of an error

finally:
    # Close the connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()
