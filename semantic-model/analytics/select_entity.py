import psycopg2
from psycopg2.extras import DictCursor
from string import Template
import argparse
import json
#from pyld import jsonld

# Database connection details
db_config = {
    "dbname": "tsdb",
    "user": "ngb",
    "password": "5t2Aop2p9Uo12Ewq5HvQZcsH2mn5Skuk",
    "host": "acid-cluster",  # or the IP of your PostgreSQL server
    "port": 5432          # default PostgreSQL port
}

# SQL query templates
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
        elif node_type == '@value':
            if row.get('attributeType').endswith('Property'):
                attribute['value'] = {
                    '@id': row.get('value')
                }
            elif row.get('attributeType').endswith('Relationship'):
                attribute['object'] = row.get('value')
        elif node_type == '@json':
            avalue = row.get('value')
        
            attribute['value'] = json.loads(avalue)
        
        attribute['observedAt'] = convertSQLDateTimeToTimestamp(row.get('observedAt'))
        attribute['modifiedAt'] = convertSQLDateTimeToTimestamp(row.get('modifiedAt'))
        
        if row['id'] in parentIds:
            for r in parentIds[row['id']]:
                add_attribute(attribute, r)

        obj[attribute_id].append(attribute)
   
    ngsild_object = {}
    erow = dict(entity_row[0])
    ngsild_object['id'] = erow['id']
    ngsild_object['type'] = erow['type']
    # Cache parentIds for nested attributes
    for row in attribute_rows:
        arow = dict(row)
        parentId = arow['parentId']
        if parentId is not None:
            if parentId not in parentIds:
                parentIds[parentId] = []
            parentIds[parentId].append(arow)
    # Process top-level attributes recursively
    for row in attribute_rows:
        arow = dict(row)
        if arow.get('parentId') is None:
            add_attribute(ngsild_object, arow)
        
    print(ngsild_object)

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Execute SQL queries using the provided 'id' and 'targetDate' values."
    )
    parser.add_argument(
        '--id',
        type=str,
        required=True,
        help="Entity id (e.g., 'urn:plasmacutter-test:1234567')"
    )
    parser.add_argument(
        '--targetDate',
        type=str,
        required=True,
        help="Target date in the format 'YYYY-MM-DD HH:MM:SS' (e.g., '2025-01-23 23:40:26')"
    )
    args = parser.parse_args()

    # Assign the command-line arguments to variables
    entity_id = args.id
    target_date = args.targetDate

    try:
        # Connect to the database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Execute the SQL query for attributes
        cursor.execute(
            sql_query_attributes.substitute(entityId=entity_id, targetDate=target_date)
        )
        attribute_rows = cursor.fetchall()
        
        # Execute the SQL query for entities
        cursor.execute(
            sql_query_entities.substitute(id=entity_id, targetDate=target_date)
        )
        entity_row = cursor.fetchall()
        
        if attribute_rows is not None and len(attribute_rows) > 0:
            # Print retrieved attribute rows
            for row in attribute_rows:
                print(dict(row))
                
            # Commit changes if needed
            conn.commit()
            print("SQL script executed successfully.")
            build_ngsild_from_sql(entity_row, attribute_rows)
        else:
            print("Nothing retrieved!")
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()  # Roll back in case of an error

    finally:
        # Close the connection and cursor
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    main()
