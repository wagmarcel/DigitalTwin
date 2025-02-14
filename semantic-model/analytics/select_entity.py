import psycopg2
from psycopg2.extras import DictCursor
import argparse
import json
from jinja2 import Template


# Database connection details
db_config = {
    "dbname": "tsdb",
    "user": "ngb",
    "password": "5t2Aop2p9Uo12Ewq5HvQZcsH2mn5Skuk",
    "host": "acid-cluster",  # or the IP of your PostgreSQL server
    "port": 5432           # default PostgreSQL port
}

def retrieve_ngsild_entities(entity_ids_list, entity_id_pattern, target_date, db_config):
    quoted_entity_ids = [f"'{eid}'" for eid in entity_ids_list] if entity_ids_list is not None else None

    # For the entities query, use the same list of ids.
    quoted_ids = quoted_entity_ids
    attributes_query = Template(sql_query_attributes_template).render(
            targetDate=target_date,
            entityIds=quoted_entity_ids,
            entityIdPattern=entity_id_pattern
        )
    entities_query = Template(sql_query_entities_template).render(
        targetDate=target_date,
        ids=quoted_ids,
        idPattern=entity_id_pattern
    )

    ngsild_entities = None
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Execute the attributes query
        cursor.execute(attributes_query)
        attribute_rows = cursor.fetchall()
        
        # Execute the entities query
        cursor.execute(entities_query)
        entity_rows = cursor.fetchall()
        
        if attribute_rows and len(attribute_rows) > 0:
            # Print retrieved attribute rows
            for row in attribute_rows:
                print(dict(row))
                
            conn.commit()
            print("SQL script executed successfully.")
            ngsild_entities = build_ngsild_from_sql(entity_rows, attribute_rows)
        else:
            print("Nothing retrieved!")
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()  # Roll back in case of an error
        raise e
    finally:
        # Close the connection and cursor
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
    return ngsild_entities
# SQL query template for attributes using Jinja2
sql_query_attributes_template = """
SELECT *
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY "id" ORDER BY "observedAt" DESC) AS row_num
  FROM attributes AS A
  WHERE "observedAt" < '{{ targetDate }}'
  {% if entityIds %}
    AND "entityId" IN ({{ entityIds | join(', ') }})
  {% endif %}
  {% if entityIdPattern %}
    AND "entityId" LIKE '{{ entityIdPattern }}'
  {% endif %}
) subquery
WHERE row_num = 1;
"""

# SQL query template for entities using Jinja2
sql_query_entities_template = """
SELECT *
FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY "id" ORDER BY "observedAt" DESC) AS row_num
  FROM entities AS A
  WHERE "observedAt" < '{{ targetDate }}'
  {% if ids %}
    AND "id" IN ({{ ids | join(', ') }})
  {% endif %}
  {% if idPattern %}
    AND "id" LIKE '{{ idPattern }}'
  {% endif %}
) subquery
WHERE row_num = 1;
"""

def convertSQLDateTimeToTimestamp(value):
    return value.strftime('%Y-%m-%dT%H:%M:%S.%f')

def build_ngsild_from_sql(entity_rows, attribute_rows):
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
        elif node_type == '@object':
            if row.get('attributeType').endswith('Property'):
                attribute['value'] = { '@id': row.get('value') }
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
   
    ngsild_objects = {}
    for entity_row in entity_rows: 
        erow = dict(entity_row)
        ngsild_object = {}
        id = erow['id']
        ngsild_object['id'] = id
        ngsild_object['type'] = erow['type']
        ngsild_objects[id] = ngsild_object

    # Build a parent-to-children mapping for nested attributes
    for row in attribute_rows:
        arow = dict(row)
        parentId = arow.get('parentId')
        if parentId is not None:
            if parentId not in parentIds:
                parentIds[parentId] = []
            parentIds[parentId].append(arow)
    
    # Process top-level attributes recursively
    for row in attribute_rows:
        arow = dict(row)
        entity_id = arow['entityId']
        ngsild_object = ngsild_objects[entity_id]
        if arow.get('parentId') is None:
            add_attribute(ngsild_object, arow)
    
    return ngsild_objects

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Execute SQL queries using provided 'id' and 'targetDate' values."
    )
    parser.add_argument(
        '--id',
        type=str,
        nargs='+',  # Allow one or more IDs
        required=False,
        help="Entity id(s) (e.g., 'urn:plasmacutter-test:1234567'). You can provide multiple IDs separated by spaces."
    )
    parser.add_argument(
        '--targetDate',
        type=str,
        required=True,
        help="Target date in the format 'YYYY-MM-DD HH:MM:SS' (e.g., '2025-01-23 23:40:26')"
    )
    parser.add_argument(
        '--entityIdPattern',
        type=str,
        required=False,
        help="Entity ID Pattern in SQL LIKE expression, e.g. ('urn:plasmacutter:%', 'h___o w___d', etc)"
    )
    args = parser.parse_args()

    if args.id is None and args.entityIdPattern is None:
        print("Either explicit ID list or ID pattern must be given.")
        exit(1)
    # Command-line values
    # args.id is now a list of one or more IDs.
    entity_ids_list = args.id
    target_date = args.targetDate

    # Optionally, set additional filter variables.
    # Quote each id for SQL if you're directly inserting them into the template.
    # Note: In production use parameterized queries to prevent SQL injection.

    # You can also set patterns if desired. Set to None if not used.
    entity_id_pattern = args.entityIdPattern

    entities = retrieve_ngsild_entities(entity_ids_list, entity_id_pattern, target_date, db_config)
    # Render SQL queries with Jinja2
    if entities is not None:
        for _, ngsild_object in entities.items(): 
            print(ngsild_object)
    else:
        print("Noting retreived")

if __name__ == '__main__':
    main()
