from rdflib import Graph, Namespace
from rdflib.namespace import RDF
import owlrl
import os
import sys
from urllib.parse import urlparse
#import yaml
import ruamel.yaml 
from ruamel.yaml.scalarstring import (DoubleQuotedScalarString as dq, 
                                      SingleQuotedScalarString as sq)
yaml = ruamel.yaml.YAML()
from jinja2 import Template

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
import configs
import utils
from sparql_to_sql import translate_sparql



alerts_bulk_table = configs.alerts_bulk_table_name
alerts_bulk_table_object = configs.alerts_bulk_table_object_name

sparql_get_all_sparql_nodes = """
PREFIX iff: <https://industry-fusion.com/types/v0.9/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
SELECT ?nodeshape ?targetclass ?message ?select ?severitylabel
where {
    ?nodeshape a sh:NodeShape .
    ?nodeshape sh:targetClass ?targetclass .
    ?nodeshape sh:sparql [ 
            sh:message ?message ;
            sh:select ?select ;
            ] ;

    OPTIONAL {
        ?nodeshape sh:sparql [
            sh:severity ?severity ;
        ] .
        ?severity iff:severityCode ?severitylabel .
    }
}

"""

sql_check_sparql_base = """
            INSERT {% if sqlite %}OR REPlACE{% endif %} INTO {{alerts_bulk_table}}
            SELECT  
            this_left AS resource,
                'SPARQLConstraintComponent({{nodeshape}})' AS event,
                'Development' AS environment,
                {% if sqlite %}
                '[SHACL Validator]' AS service,
                {% else %}
                ARRAY ['SHACL Validator'] AS service,
                {% endif %}
                CASE WHEN this IS NOT NULL
                    THEN '{{severity}}' 
                    ELSE 'ok' END AS severity,
                'customer'  customer,
                CASE WHEN this IS NOT NULL
                THEN '{{message}}'
                ELSE 'All ok' END  as `text`
                {%- if sqlite %}
                ,CURRENT_TIMESTAMP
                {%- endif %}
            
            FROM (SELECT A.this as this_left, B.this as this FROM (SELECT id as this from {{targetclass}}_view) as A LEFT JOIN ({{sql_expression}}) as B ON A.this = B.this)
"""


def strip_class(klass):
        a = urlparse(klass)
        return os.path.basename(a.path)    


def translate(shaclfile, knowledgefile):
    """
    Translate shacl properties into SQL constraints.

    Parameters:
        shaclname: filename of SHACL file
        knowledgename: filename of knowledge file

    Returns:
        sql-statement-list: list of plain SQL objects 
        (statementset, tables, views): statementset in yaml format

    """
    g = Graph()
    h = Graph()
    g.parse(shaclfile)
    h.parse(knowledgefile)
    g += h
    rdfs = owlrl.RDFSClosure.RDFS_Semantics(g, axioms=False, daxioms=False, rdfs=False).closure()
    sh = Namespace("http://www.w3.org/ns/shacl#")
    tables = [alerts_bulk_table_object, configs.attributes_table_obj_name, configs.rdf_table_obj_name]
    views = [configs.attributes_view_obj_name]
    statementsets = []
    sqlite = ''
    # Get all NGSI-LD Relationship
    qres = g.query(sparql_get_all_sparql_nodes)
    for row in qres:
        #print(row)
        target_class = row.targetclass
        message = row.message.toPython() if row.message else None
        select = row.select.toPython() if row.select else None
        nodeshape = strip_class(row.nodeshape.toPython()) if row.nodeshape else None
        targetclass = utils.class_to_obj_name(strip_class(row.targetclass.toPython())) if row.targetclass else None
        severitylabel = row.severitylabel.toPython() if row.severitylabel is not None else 'warning'
        sql_expression, tables = translate_sparql(shaclfile, knowledgefile, select, target_class)
        sql_command_yaml = Template(sql_check_sparql_base).render(
                alerts_bulk_table = alerts_bulk_table,
                sql_expression = sql_expression,
                targetclass = targetclass,
                message = message,
                nodeshape = nodeshape,
                severity = severitylabel,
                sqlite = False
        )
        sql_command_sqlite = Template(sql_check_sparql_base).render(
                alerts_bulk_table = alerts_bulk_table,
                sql_expression = sql_expression,
                targetclass = targetclass,
                message = message,
                nodeshape = nodeshape,
                severity = severitylabel,
                sqlite = True
        )
        
        sql_command_sqlite += ";"
        sql_command_yaml += ";"
        sqlite += sql_command_sqlite
        statementsets.append(sql_command_yaml)
    views = []
    tables = list(set(tables))
    for table in tables:
        views.append(f'{table}-view')
    tables.append(alerts_bulk_table_object)
    tables.append(configs.rdf_table_name)
    return sqlite, (statementsets, tables, views)
        #sql_command_sqlite += ";"
        #sql_command_yaml += ";"
        #statementsets.append(sql_command_yaml)
        #table_obj = utils.camelcase_to_snake_case(target_class)
        #target_class_obj = utils.class_to_obj_name(target_class)
        #if target_class_obj not in tables:
        #    tables.append(target_class_obj)
        #    views.append(target_class_obj + "-view")
        #return statementsets, (statementsets, tables, views)