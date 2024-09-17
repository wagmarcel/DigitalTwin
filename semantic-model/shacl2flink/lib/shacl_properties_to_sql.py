from rdflib import Graph, Namespace
from rdflib.namespace import SH
import os
import sys
import csv
from io import StringIO
import ruamel.yaml
from jinja2 import Template

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
import configs  # noqa: E402
import utils  # noqa: E402


yaml = ruamel.yaml.YAML()

alerts_bulk_table = configs.alerts_bulk_table_name
alerts_bulk_table_object = configs.alerts_bulk_table_object_name

sparql_get_all_relationships = """
SELECT ?nodeshape ?targetclass ?propertypath ?mincount ?maxcount ?attributeclass ?severitycode
where {
    ?nodeshape a sh:NodeShape .
    ?nodeshape sh:targetClass ?targetclass .
    ?nodeshape sh:property [
        sh:path ?propertypath ;
        sh:property [
            sh:path ngsi-ld:hasObject ;
            sh:class ?attributeclass ;
        ]
    ] .
    OPTIONAL{?nodeshape sh:property [ sh:path ?propertypath; sh:maxCount ?maxcount ]}
    OPTIONAL{?nodeshape sh:property [ sh:path ?propertypath; sh:minCount ?mincount ]}
    OPTIONAL {
        ?nodeshape sh:property [
            sh:path ?propertypath;
            sh:severity ?severity ;
        ] .
        ?severity rdfs:label ?severitycode .
    }
}
order by ?targetclass
"""  # noqa: E501

sparql_get_all_properties = """
SELECT
    ?nodeshape ?targetclass ?propertypath ?mincount ?maxcount ?attributeclass ?nodekind
    ?minexclusive ?maxexclusive ?mininclusive ?maxinclusive ?minlength ?maxlength ?pattern ?severitycode
    (GROUP_CONCAT(CONCAT('"',?in, '"'); separator=',') as ?ins)
where {
    ?nodeshape a sh:NodeShape .
    ?nodeshape sh:targetClass ?targetclass .
    ?nodeshape sh:property [
        sh:path ?propertypath ;
        sh:property [
            sh:path ngsi-ld:hasValue ;
            sh:nodeKind ?nodekind ;
        ] ;

    ] .
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:minCount ?mincount ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:maxCount ?maxcount ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:property [sh:path ngsi-ld:hasValue ; sh:minExclusive ?minexclusive ;] ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:property [sh:path ngsi-ld:hasValue ; sh:maxExclusive ?maxexclusive ;] ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:property [sh:path ngsi-ld:hasValue ; sh:minInclusive ?mininclusive ;] ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:property [sh:path ngsi-ld:hasValue ; sh:maxInclusive ?maxinclusive ;] ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:property [sh:path ngsi-ld:hasValue ; sh:minLength ?minlength ;] ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:property [sh:path ngsi-ld:hasValue ; sh:maxLength ?maxlength ;] ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:property [sh:path ngsi-ld:hasValue ; sh:pattern ?pattern ;] ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:property [sh:path ngsi-ld:hasValue ; sh:in/(rdf:rest*/rdf:first)+ ?in ;] ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath ; sh:property [sh:path ngsi-ld:hasValue ; sh:class ?attributeclass ;] ; ] }
    OPTIONAL { ?nodeshape sh:property [ sh:path ?propertypath; sh:severity ?severity ; ] . ?severity rdfs:label ?severitycode .}
}
GROUP BY ?nodeshape ?targetclass ?propertypath ?mincount ?maxcount ?attributeclass ?nodekind
    ?minexclusive ?maxexclusive ?mininclusive ?maxinclusive ?minlength ?maxlength ?pattern ?severitycode
order by ?targetclass

"""  # noqa: E501
sql_check_relationship_base = """
            INSERT {% if sqlite %}OR REPlACE{% endif %} INTO {{alerts_bulk_table}}
            WITH A1 as (
                    SELECT A.id AS this,
                           A.`type` as typ,
                           C.`type` AS entity,
                           B.`type` AS link,
                           B.`nodeType` as nodeType,
                    IFNULL(B.`index`, 0) as `index`,
                    D.targetClass as targetClass,
                    D.propertyPath as propertyPath,
                    D.propertyClass as propertyClass,
                    D.maxCount as maxCount,
                    D.minCount as minCount,
                    D.severity as severity 
                    FROM {{target_class}}_view AS A JOIN `relationshipChecksTable` as D ON A.`type` = D.targetClass
                    LEFT JOIN attributes_view AS B ON B.name = D.propertyPath
                    LEFT JOIN {{target_class}}_view AS C ON B.`https://uri.etsi.org/ngsi-ld/hasObject` = C.id
                    WHERE
                        (B.entityId = A.id OR B.entityId IS NULL)
                        AND (B.name = D.propertyPath OR B.name IS NULL)

            )
"""  # noqa: E501

sql_check_relationship_property_class = """
            SELECT this AS resource,
                'ClassConstraintComponent(' || `propertyPath` || '[' || CAST( `index` AS STRING) || '])' AS event,
                'Development' AS environment,
                {% if sqlite %}
                '[SHACL Validator]' AS service,
                {% else %}
                ARRAY ['SHACL Validator'] AS service,
                {% endif %}
                CASE WHEN typ IS NOT NULL AND link IS NOT NULL AND entity IS NULL THEN `severity`
                    ELSE 'ok' END AS severity,
                'customer'  customer,

                CASE WHEN typ IS NOT NULL AND link IS NOT NULL AND entity IS NULL
                        THEN 'Model validation for relationship' || `propertyPath` || 'failed for '|| this || '. Relationship not linked to existing entity of type ' ||  `propertyClass` || '.'
                    ELSE 'All ok' END as `text`
                {%- if sqlite %}
                ,CURRENT_TIMESTAMP
                {%- endif %}
            FROM A1 WHERE A1.propertyClass IS NOT NULL
"""  # noqa: E501

sql_check_relationship_property_count = """
            SELECT this AS resource,
                'CountConstraintComponent(' || `propertyPath` || ')' AS event,
                'Development' AS environment,
                {% if sqlite %}
                '[SHACL Validator]' AS service,
                {% else %}
                ARRAY ['SHACL Validator'] AS service,
                {% endif %}
                CASE WHEN typ IS NOT NULL AND (count(link) > `maxCount` OR count(link) < `minCount`)
                    THEN `severity`
                    ELSE 'ok' END AS severity,
                'customer'  customer,
                CASE WHEN typ IS NOT NULL AND (count(link) > `maxCount`  OR count(link) < `mincount`)
                    THEN
                        'Model validation for relationship ' || `propertyPath` || 'failed for ' || this || ' . Found ' || CAST(count(link) AS STRING) || ' relationships instead of
                            [' || `mincount` || ', ' || `maxcount` || ']!'
                    ELSE 'All ok' END as `text`
                {%- if sqlite %}
                ,CURRENT_TIMESTAMP
                {%- endif %}
            FROM A1 WHERE `minCount` is NOT NULL or `maxCount` is NOT NULL
            group by this, typ, propertyPath 
"""  # noqa: E501

sql_check_relationship_nodeType = """
            SELECT this AS resource,
                'NodeKindConstraintComponent(' || `propertyPath` || ')' AS event,
                'Development' AS environment,
                {% if sqlite %}
                '[SHACL Validator]' AS service,
                {% else %}
                ARRAY ['SHACL Validator'] AS service,
                {% endif %}
                CASE WHEN typ IS NOT NULL AND link IS NOT NULL AND (nodeType is NULL OR nodeType <> '{{ property_nodetype }}')
                    THEN `severity`
                    ELSE 'ok' END AS severity,
                'customer'  customer,
                CASE WHEN typ IS NOT NULL AND  link IS NOT NULL AND (nodeType is NULL OR nodeType <> '{{ property_nodetype }}')
                    THEN
                        'Model validation for relationship ' || `propertyPath` || ' failed for ' || this || ' . NodeType is '|| nodeType || ' but must be an IRI.'
                    ELSE 'All ok' END as `text`
                {%- if sqlite %}
                ,CURRENT_TIMESTAMP
                {%- endif %}
            FROM A1
"""  # noqa: E501

sql_check_property_iri_base = """
INSERT {% if sqlite %} OR REPlACE{% endif %} INTO {{alerts_bulk_table}}
WITH A1 AS (SELECT A.id as this,
                   A.`type` as typ,
                   B.`https://uri.etsi.org/ngsi-ld/hasValue` as val,
                   B.`nodeType` as nodeType,
                   B.`type` as attr_typ,
                   C.subject as foundVal,
                   C.object as foundClass,
                   IFNULL(B.`index`, 0) as `index`,
                   D.propertyPath as propertyPath,
                   D.propertyClass as propertyClass,
                   D.propertyNodeType as propertyNodeType,
                   D.maxCount as maxCount,
                   D.minCount as minCount,
                   D.severity as severity,
                   D.minExclusive as minExclusive,
                   D.maxExclusive as maxExclusive,
                   D.minInclusive as minInclusive,
                   D.maxInclusive as maxInclusive,
                   D.minLength as minLength,
                   D.maxLength as maxLength,
                   D.pattern as pattern 
                   FROM `{{target_class}}_view` AS A JOIN `propertyChecksTable` as D ON A.`type` = D.targetClass
            LEFT JOIN attributes_view AS B ON D.propertyPath = B.name
            LEFT JOIN {{rdf_table_name}} as C ON C.subject = '<' || B.`https://uri.etsi.org/ngsi-ld/hasValue` || '>'
                and C.predicate = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>' and C.object = D.propertyPath
            )
"""  # noqa: E501

sql_check_property_count = """
SELECT this AS resource,
    'CountConstraintComponent({{property_path}})' AS event,
    'Development' AS environment,
    {%- if sqlite %}
    '[SHACL Validator]' AS service,
    {%- else %}
    ARRAY ['SHACL Validator'] AS service,
    {%- endif %}
    CASE WHEN typ IS NOT NULL AND ({%- if maxcount %} count(attr_typ) > {{maxcount}} {%- endif %} {%- if mincount and maxcount %} OR {%- endif %} {%- if mincount %} count(attr_typ) < {{mincount}} {%- endif %})
        THEN '{{severity}}'
        ELSE 'ok' END AS severity,
    'customer'  customer,
    CASE WHEN typ IS NOT NULL AND ({%- if maxcount %} count(attr_typ) > {{maxcount}} {%- endif %} {%- if mincount and maxcount %} OR {%- endif %} {%- if mincount %} count(attr_typ) < {{mincount}} {%- endif %})
        THEN 'Model validation for Property {{property_path}} failed for ' || this || '.  Found ' || CAST(count(attr_typ) AS STRING) || ' relationships instead of
                            [{%- if mincount %}{{mincount}}{%- else %} 0 {%- endif %},{%if maxcount %}{{maxcount}}]{%- else %}[ {%- endif %}!'
        ELSE 'All ok' END as `text`
        {% if sqlite %}
        ,CURRENT_TIMESTAMP
        {% endif %}
FROM A1 group by this, typ
"""  # noqa: E501

sql_check_property_iri_class = """
SELECT this AS resource,
    'DatatypeConstraintComponent({{property_path}}[' || CAST( `index` AS STRING) || '])' AS event,
    'Development' AS environment,
    {%- if sqlite %}
    '[SHACL Validator]' AS service,
    {%- else %}
    ARRAY ['SHACL Validator'] AS service,
    {%- endif %}
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND (val is NULL OR foundVal is NULL)
        THEN '{{severity}}'
        ELSE 'ok' END AS severity,
    'customer'  customer,
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND (val is NULL OR foundVal is NULL)
        THEN 'Model validation for Property {{property_path}} failed for ' || this || '. Invalid value ' || IFNULL(val, 'NULL') || ' not type of {{property_class}}'
        ELSE 'All ok' END as `text`
        {% if sqlite %}
        ,CURRENT_TIMESTAMP
        {% endif %}
FROM A1
"""  # noqa: E501

sql_check_property_nodeType = """
SELECT this AS resource,
 'NodeKindConstraintComponent(' || `propertyPath` || '[' || CAST( `index` AS STRING) || '])' AS event,
    'Development' AS environment,
     {%- if sqlite -%}
    '[SHACL Validator]' AS service,
    {%- else %}
    ARRAY ['SHACL Validator'] AS service,
    {%- endif %}
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND (nodeType is NULL OR nodeType <> `propertyNodetype`)
        THEN `severity`
        ELSE 'ok' END AS severity,
    'customer'  customer,
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND (nodeType is NULL OR nodeType <> `propertyNodetype`)
        THEN 'Model validation for Property ' || `propertyPath` || ' failed for ' || this || '. Node is not ' || 
            CASE WHEN `propertyNodetype` = '@id' THEN ' an IRI' ELSE 'a Literal' END
        ELSE 'All ok' END as `text`
        {% if sqlite %}
        ,CURRENT_TIMESTAMP
        {% endif %}
FROM A1 WHERE propertyNodetype IS NOT NULL
"""  # noqa: E501

sql_check_property_minmax = """
SELECT this AS resource,
 '{{minmaxname}}ConstraintComponent({{property_path}}[' || CAST( `index` AS STRING) || '])' AS event,
    'Development' AS environment,
     {%- if sqlite -%}
    '[SHACL Validator]' AS service,
    {%- else %}
    ARRAY ['SHACL Validator'] AS service,
    {%- endif %}
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND (CAST(val AS DOUBLE) is NULL or NOT (CAST(val as DOUBLE) {{ operator }} {{ comparison_value }}) )
        THEN '{{severity}}'
        ELSE 'ok' END AS severity,
    'customer'  customer,
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND (CAST(val AS DOUBLE) is NULL)
        THEN 'Model validation for Property {{property_path}} failed for ' || this || '. Value ' || IFNULL(val, 'NULL') || ' not comparable with {{ comparison_value }}.'
        WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND NOT (CAST(val as DOUBLE) {{ operator }} {{ comparison_value }})
        THEN 'Model validation for Property {{property_path}} failed for ' || this || '. Value ' || IFNULL(val, 'NULL') || ' is not {{ operator }} {{ comparison_value }}.'
        ELSE 'All ok' END as `text`
        {% if sqlite %}
        ,CURRENT_TIMESTAMP
        {% endif %}
FROM A1
"""  # noqa: E501

sql_check_string_length = """
SELECT this AS resource,
 '{{minmaxname}}ConstraintComponent({{property_path}}[' || CAST( `index` AS STRING) || '])' AS event,
    'Development' AS environment,
     {%- if sqlite -%}
    '[SHACL Validator]' AS service,
    {%- else %}
    ARRAY ['SHACL Validator'] AS service,
    {%- endif %}
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND {%- if sqlite %} LENGTH(val) {%- else  %} CHAR_LENGTH(val) {%- endif %} {{ operator }} {{ comparison_value }}
        THEN '{{severity}}'
        ELSE 'ok' END AS severity,
    'customer'  customer,
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND {%- if sqlite %} LENGTH(val) {%- else  %} CHAR_LENGTH(val) {%- endif %} {{ operator }} {{ comparison_value }}
        THEN 'Model validation for Property {{property_path}} failed for ' || this || '. Length of ' || IFNULL(val, 'NULL') || ' is {{ operator }} {{ comparison_value }}.'
        ELSE 'All ok' END as `text`
        {% if sqlite %}
        ,CURRENT_TIMESTAMP
        {% endif %}
FROM A1
"""  # noqa: E501

sql_check_literal_pattern = """
SELECT this AS resource,
 '{{validationname}}ConstraintComponent({{property_path}}[' || CAST( `index` AS STRING) || '])' AS event,
    'Development' AS environment,
     {%- if sqlite -%}
    '[SHACL Validator]' AS service,
    {%- else %}
    ARRAY ['SHACL Validator'] AS service,
    {%- endif %}
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND {%- if sqlite %} NOT (val REGEXP '{{pattern}}') {%- else  %} NOT REGEXP(val, '{{pattern}}') {%- endif %}
        THEN '{{severity}}'
        ELSE 'ok' END AS severity,
    'customer'  customer,
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND {%- if sqlite %} NOT (val REGEXP '{{pattern}}') {%- else  %} NOT REGEXP(val, '{{pattern}}') {%- endif %}
        THEN 'Model validation for Property {{property_path}} failed for ' || this || '. Value ' || IFNULL(val, 'NULL') || ' does not match pattern {{ pattern }}'
        ELSE 'All ok' END as `text`
        {% if sqlite %}
        ,CURRENT_TIMESTAMP
        {% endif %}
FROM A1
"""  # noqa: E501

sql_check_literal_in = """
SELECT this AS resource,
 '{{constraintname}}({{property_path}}[' || CAST( `index` AS STRING) || '])' AS event,
    'Development' AS environment,
     {%- if sqlite -%}
    '[SHACL Validator]' AS service,
    {%- else %}
    ARRAY ['SHACL Validator'] AS service,
    {%- endif %}
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND val NOT IN ({% for elem in ins %}'{{ elem }}'{{ ", " if not loop.last else "" }}{% endfor %})
        THEN '{{severity}}'
        ELSE 'ok' END AS severity,
    'customer'  customer,
    CASE WHEN typ IS NOT NULL AND attr_typ IS NOT NULL AND val NOT IN ({% for elem in ins %}'{{ elem }}'{{ ", " if not loop.last else "" }}{% endfor %})
        THEN 'Model validation for Property {{property_path}} failed for ' || this || '. Value ' || IFNULL(val, 'NULL') || ' is not allowed.'
        ELSE 'All ok' END as `text`
        {% if sqlite %}
        ,CURRENT_TIMESTAMP
        {% endif %}
FROM A1
"""  # noqa: E501


def translate(shaclefile, knowledgefile, prefixes):
    """
    Translate shacl properties into SQL constraints.

    Parameters:
        filename: filename of SHACL file

    Returns:
        sql-statement-list: list of plain SQL objects
        (statementset, tables, views): statementset in yaml format

    """
    g = Graph()
    h = Graph()
    g.parse(shaclefile)
    h.parse(knowledgefile)
    g += h
    sh = Namespace("http://www.w3.org/ns/shacl#")
    tables = [alerts_bulk_table_object, configs.attributes_table_obj_name,
              configs.rdf_table_obj_name]
    views = [configs.attributes_view_obj_name]
    statementsets = []
    sqlite = ''
    # Get all NGSI-LD Relationship
    sql_command_yaml = Template(sql_check_relationship_base).render(
        alerts_bulk_table=alerts_bulk_table,
        target_class="entity",
        sqlite=False)
    sql_command_sqlite = Template(sql_check_relationship_base).render(
        alerts_bulk_table=alerts_bulk_table,
        target_class="entity",
        sqlite=True)
    sql_command_yaml += \
        Template(sql_check_relationship_property_class).render(
            alerts_bulk_table=alerts_bulk_table,
            target_class="entity",
            sqlite=False)
    sql_command_sqlite += \
        Template(sql_check_relationship_property_class).render(
            alerts_bulk_table=alerts_bulk_table,
            target_class="entity",
            sqlite=True)
    sql_command_yaml += "\nUNION ALL"
    sql_command_sqlite += "\nUNION ALL"
    sql_command_yaml += \
        Template(sql_check_relationship_property_count).render(
            alerts_bulk_table=alerts_bulk_table,
            target_class="entity",
            sqlite=False)
    sql_command_sqlite += \
        Template(sql_check_relationship_property_count).render(
            alerts_bulk_table=alerts_bulk_table,
            target_class="entity",
            sqlite=True)
    sql_command_yaml += "\nUNION ALL"
    sql_command_sqlite += "\nUNION ALL"
    sql_command_yaml += Template(sql_check_relationship_nodeType).render(
        alerts_bulk_table=alerts_bulk_table,
        property_nodetype='@id',
        property_nodetype_description='an IRI',
        sqlite=False
    )
    sql_command_sqlite += Template(sql_check_relationship_nodeType).render(
        alerts_bulk_table=alerts_bulk_table,
        property_nodetype='@id',
        property_nodetype_description='an IRI',
        sqlite=True
    )
    sql_command_sqlite += ";"
    sql_command_yaml += ";"


    statementsets.append(sql_command_yaml)
    sqlite += sql_command_sqlite
    sql_command_yaml = Template(sql_check_property_iri_base).render(
    alerts_bulk_table=alerts_bulk_table,
    target_class="entity",
    rdf_table_name=configs.rdf_table_name,
    sqlite=False
    )
    sql_command_sqlite = Template(sql_check_property_iri_base).render(
        alerts_bulk_table=alerts_bulk_table,
        target_class="entity",
        rdf_table_name=configs.rdf_table_name,
        sqlite=True
    )
    sql_command_yaml += Template(sql_check_property_nodeType).render(
    alerts_bulk_table=alerts_bulk_table,
    sqlite=False
    )
    sql_command_sqlite += Template(sql_check_property_nodeType).render(
        alerts_bulk_table=alerts_bulk_table,
        sqlite=True
    )
    sql_command_sqlite += ";"
    sql_command_yaml += ";"
    sqlite += sql_command_sqlite
    statementsets.append(sql_command_yaml)
    qres = g.query(sparql_get_all_relationships, initNs=prefixes)    
    relationshp_checks = []
    for row in qres:
        check = {}
        #target_class = utils.camelcase_to_snake_case(utils.strip_class(row.targetclass.toPython())) \
        #    if row.targetclass else None
        target_class = row.targetclass.toPython() \
            if row.targetclass else None
        property_path = row.propertypath.toPython() if row.propertypath \
            else None
        property_class = row.attributeclass.toPython() if row.attributeclass \
            else None
        mincount = row.mincount.toPython() if row.mincount else 0
        maxcount = row.maxcount.toPython() if row.maxcount else None
        severitycode = row.severitycode.toPython() if row.severitycode \
            else 'warning'
        check['targetClass'] = target_class
        check['propertyPath'] = property_path
        check['propertyClass'] = property_class
        check['maxCount'] = maxcount
        check['minCount'] = mincount
        check['severity'] = severitycode
 
        # if add_union:
        #     sql_command_yaml += "\nUNION ALL"
        #     sql_command_sqlite += "\nUNION ALL"
        # sql_command_yaml += Template(sql_check_relationship_nodeType).render(
        #     alerts_bulk_table=alerts_bulk_table,
        #     target_class=target_class,
        #     property_path=property_path,
        #     severity=severitycode,
        #     property_nodetype='@id',
        #     property_nodetype_description='an IRI',
        #     sqlite=False
        # )
        # sql_command_sqlite += Template(sql_check_relationship_nodeType).render(
        #     alerts_bulk_table=alerts_bulk_table,
        #     target_class=target_class,
        #     property_path=property_path,
        #     severity=severitycode,
        #     property_nodetype='@id',
        #     property_nodetype_description='an IRI',
        #     sqlite=True
        # )
        #sql_command_sqlite += ";"
        #sql_command_yaml += ";"
        #statementsets.append(sql_command_yaml)
        #sqlite += sql_command_sqlite

        target_class_obj = utils.class_to_obj_name(target_class)
        target_class_obj = utils.class_to_obj_name(target_class)
        if target_class_obj not in tables:
            tables.append(target_class_obj)
            views.append(target_class_obj + "-view")
        target_class_obj = \
            utils.class_to_obj_name(utils.strip_class(property_class))
        if target_class_obj not in tables:
            tables.append(target_class_obj)
            views.append(target_class_obj + "-view")
        relationshp_checks.append(check)
    # Get all NGSI-LD Properties
    qres = g.query(sparql_get_all_properties, initNs=prefixes)
    #qres = []
    property_checks = []
    for row in qres:
        check = {}
        nodeshape = row.nodeshape.toPython()
        target_class = row.targetclass.toPython() \
            if row.targetclass else None
        property_path = row.propertypath.toPython() if row.propertypath \
            else None
        property_class = row.attributeclass.toPython() if row.attributeclass\
            else None
        mincount = row.mincount.toPython() if row.mincount else 0
        maxcount = row.maxcount.toPython() if row.maxcount else None
        severitycode = row.severitycode.toPython() if row.severitycode \
            else 'warning'
        nodekind = row.nodekind
        min_exclusive = row.minexclusive.toPython() if row.minexclusive \
            is not None else None
        max_exclusive = row.maxexclusive.toPython() if row.maxexclusive \
            else None
        min_inclusive = row.mininclusive.toPython() if row.mininclusive \
            is not None else None
        max_inclusive = row.maxinclusive.toPython() if row.maxinclusive \
            else None
        min_length = row.minlength.toPython() if row.minlength is not None \
            else None
        max_length = row.maxlength.toPython() if row.maxlength is not None \
            else None
        pattern = row.pattern.toPython() if row.pattern is not None else None
        ins = row.ins.toPython() if row.ins is not None else None
        if ins is not None and ins != '':
            reader = csv.reader(StringIO(ins))
            parsed_list = next(reader)
            ins = [element.replace("'", "\\'") for element in parsed_list]
        check['targetClass'] = target_class
        check['propertyPath'] = property_path
        check['propertyClass'] = property_class
        check['propertyNodetype'] = '@id' if nodekind == SH.IRI else '@value'
        check['maxCount'] = maxcount
        check['minCount'] = mincount
        check['severity'] = severitycode
        check['minExclusive'] = min_exclusive
        check['maxExclusive'] = max_exclusive
        check['minInclusive'] = min_inclusive
        check['maxInclusive'] = max_inclusive
        check['minLength'] = min_length
        check['maxLength'] = max_length
        check['pattern'] = pattern
        check['ins'] = ins
        property_checks.append(check)
        # if (nodekind == sh.IRI):
 

        #     if property_class:
        #         sql_command_yaml += "\nUNION ALL"
        #         sql_command_sqlite += "\nUNION ALL"
        #         sql_command_yaml += \
        #             Template(sql_check_property_iri_class).render(
        #                 alerts_bulk_table=alerts_bulk_table,
        #                 target_class=target_class,
        #                 property_path=property_path,
        #                 property_class=property_class,
        #                 severity=severitycode,
        #                 sqlite=False)
        #         sql_command_sqlite += \
        #             Template(sql_check_property_iri_class).render(
        #                 alerts_bulk_table=alerts_bulk_table,
        #                 target_class=target_class,
        #                 property_path=property_path,
        #                 property_class=property_class,
        #                 severity=severitycode,
        #                 sqlite=True)
        # elif (nodekind == sh.Literal):
        #     sql_command_yaml = Template(sql_check_property_iri_base).render(
        #         alerts_bulk_table=alerts_bulk_table,
        #         target_class=target_class,
        #         property_path=property_path,
        #         property_class=property_class,
        #         rdf_table_name=configs.rdf_table_name,
        #         severity=severitycode,
        #         sqlite=False
        #     )
        #     sql_command_sqlite = Template(sql_check_property_iri_base).render(
        #         alerts_bulk_table=alerts_bulk_table,
        #         target_class=target_class,
        #         property_path=property_path,
        #         property_class=property_class,
        #         rdf_table_name=configs.rdf_table_name,
        #         severity=severitycode,
        #         sqlite=True
        #     )
        #     sql_command_yaml += Template(sql_check_property_nodeType).render(
        #         alerts_bulk_table=alerts_bulk_table,
        #         target_class=target_class,
        #         property_path=property_path,
        #         severity=severitycode,
        #         property_nodetype='@value',
        #         property_nodetype_description='a Literal',
        #         sqlite=False
        #     )
        #     sql_command_sqlite += Template(sql_check_property_nodeType).render(
        #         alerts_bulk_table=alerts_bulk_table,
        #         target_class=target_class,
        #         property_path=property_path,
        #         severity=severitycode,
        #         property_nodetype='@value',
        #         property_nodetype_description='a Literal',
        #         sqlite=True
        #     )
        #     if min_exclusive is not None:
        #         sql_command_yaml += "\nUNION ALL"
        #         sql_command_sqlite += "\nUNION ALL"
        #         sql_command_yaml += Template(sql_check_property_minmax).render(
        #             target_class=target_class,
        #             property_path=property_path,
        #             operator='>',
        #             comparison_value=min_exclusive,
        #             severity=severitycode,
        #             minmaxname="MinExclusive",
        #             sqlite=False
        #         )
        #         sql_command_sqlite += \
        #             Template(sql_check_property_minmax).render(
        #                 target_class=target_class,
        #                 property_path=property_path,
        #                 operator='>',
        #                 comparison_value=min_exclusive,
        #                 severity=severitycode,
        #                 minmaxname="MinExclusive",
        #                 sqlite=True)
        #     if ins is not None and len(ins) != 0:
        #         sql_command_yaml += "\nUNION ALL"
        #         sql_command_sqlite += "\nUNION ALL"
        #         sql_command_yaml += \
        #             Template(sql_check_literal_in).render(
        #                 alerts_bulk_table=alerts_bulk_table,
        #                 target_class=target_class,
        #                 property_path=property_path,
        #                 property_class=property_class,
        #                 severity=severitycode,
        #                 sqlite=False,
        #                 constraintname="InConstraintComponent",
        #                 ins=ins)
        #         sql_command_sqlite += \
        #             Template(sql_check_literal_in).render(
        #                 alerts_bulk_table=alerts_bulk_table,
        #                 target_class=target_class,
        #                 property_path=property_path,
        #                 property_class=property_class,
        #                 severity=severitycode,
        #                 sqlite=True,
        #                 constraintname="InConstraintComponent",
        #                 ins=ins)
        #     if max_exclusive is not None:
        #         sql_command_yaml += "\nUNION ALL"
        #         sql_command_sqlite += "\nUNION ALL"
        #         sql_command_yaml += Template(sql_check_property_minmax).render(
        #             target_class=target_class,
        #             property_path=property_path,
        #             operator='<',
        #             comparison_value=max_exclusive,
        #             severity=severitycode,
        #             minmaxname="MaxExclusive",
        #             sqlite=False
        #         )
        #         sql_command_sqlite += \
        #             Template(sql_check_property_minmax).render(
        #                 target_class=target_class,
        #                 property_path=property_path,
        #                 operator='<',
        #                 comparison_value=max_exclusive,
        #                 severity=severitycode,
        #                 minmaxname="MaxExclusive",
        #                 sqlite=True)
        #     if max_inclusive is not None:
        #         sql_command_yaml += "\nUNION ALL"
        #         sql_command_sqlite += "\nUNION ALL"
        #         sql_command_yaml += Template(sql_check_property_minmax).render(
        #             target_class=target_class,
        #             property_path=property_path,
        #             operator='<=',
        #             comparison_value=max_inclusive,
        #             severity=severitycode,
        #             minmaxname="MaxInclusive",
        #             sqlite=False
        #         )
        #         sql_command_sqlite += \
        #             Template(sql_check_property_minmax).render(
        #                 target_class=target_class,
        #                 property_path=property_path,
        #                 operator='<=',
        #                 comparison_value=max_inclusive,
        #                 severity=severitycode,
        #                 minmaxname="MaxInclusive",
        #                 sqlite=True)
        #     if min_inclusive is not None:
        #         sql_command_yaml += "\nUNION ALL"
        #         sql_command_sqlite += "\nUNION ALL"
        #         sql_command_yaml += Template(sql_check_property_minmax).render(
        #             target_class=target_class,
        #             property_path=property_path,
        #             operator='>=',
        #             comparison_value=min_inclusive,
        #             severity=severitycode,
        #             minmaxname="MinInclusive",
        #             sqlite=False
        #         )
        #         sql_command_sqlite += \
        #             Template(sql_check_property_minmax).render(
        #                 target_class=target_class,
        #                 property_path=property_path,
        #                 operator='>=',
        #                 comparison_value=min_inclusive,
        #                 severity=severitycode,
        #                 minmaxname="MinInclusive",
        #                 sqlite=True)
        #     if pattern is not None:
        #         sql_command_yaml += "\nUNION ALL"
        #         sql_command_sqlite += "\nUNION ALL"
        #         sql_command_yaml += Template(sql_check_literal_pattern).render(
        #             property_path=property_path,
        #             pattern=pattern,
        #             severity=severitycode,
        #             validationname="Pattern",
        #             sqlite=False
        #         )
        #         sql_command_sqlite += \
        #             Template(sql_check_literal_pattern).render(
        #                 property_path=property_path,
        #                 pattern=pattern,
        #                 severity=severitycode,
        #                 validationname="Pattern",
        #                 sqlite=True)

        # else:
        #     print(f'WARNING: Property path {property_path} of Nodeshape \
        #           {nodeshape} is neither IRI nor Literal')
        #     continue
        # if mincount > 0 or maxcount:
        #     sql_command_yaml += "\nUNION ALL"
        #     sql_command_sqlite += "\nUNION ALL"
        #     sql_command_yaml += Template(sql_check_property_count).render(
        #         target_class=target_class,
        #         property_path=property_path,
        #         mincount=mincount,
        #         maxcount=maxcount,
        #         severity=severitycode,
        #         sqlite=False
        #     )
        #     sql_command_sqlite += \
        #         Template(sql_check_property_count).render(
        #             target_class=target_class,
        #             property_path=property_path,
        #             mincount=mincount,
        #             maxcount=maxcount,
        #             severity=severitycode,
        #             sqlite=True)
        # if min_length is not None:
        #     sql_command_yaml += "\nUNION ALL"
        #     sql_command_sqlite += "\nUNION ALL"
        #     sql_command_yaml += Template(sql_check_string_length).render(
        #         property_path=property_path,
        #         operator='<',
        #         comparison_value=min_length,
        #         minmaxname="MinLength",
        #         severity=severitycode,
        #         sqlite=False
        #     )
        #     sql_command_sqlite += Template(sql_check_string_length).render(
        #         property_path=property_path,
        #         operator='<',
        #         comparison_value=min_length,
        #         minmaxname="MinLength",
        #         severity=severitycode,
        #         sqlite=True
        #     )
        # if max_length is not None:
        #     sql_command_yaml += "\nUNION ALL"
        #     sql_command_sqlite += "\nUNION ALL"
        #     sql_command_yaml += Template(sql_check_string_length).render(
        #         property_path=property_path,
        #         operator='>',
        #         comparison_value=max_length,
        #         minmaxname="MaxLength",
        #         severity=severitycode,
        #         sqlite=False
        #     )
        #     sql_command_sqlite += Template(sql_check_string_length).render(
        #         property_path=property_path,
        #         operator='>',
        #         comparison_value=max_length,
        #         minmaxname="MaxLength",
        #         severity=severitycode,
        #         sqlite=True
        #     )
        # sql_command_sqlite += ";"
        # sql_command_yaml += ";"
        # sqlite += sql_command_sqlite
        # statementsets.append(sql_command_yaml)
        # target_class_obj = utils.class_to_obj_name(target_class)
        # if target_class_obj not in tables:
        #     tables.append(target_class_obj)
        #     views.append(target_class_obj + "-view")
    sqlite += '\n'
    sqlite += utils.add_relationship_checks(relationshp_checks, utils.SQL_DIALECT.SQLITE)
    sqlite += '\n'
    sqlite += utils.add_property_checks(property_checks, utils.SQL_DIALECT.SQLITE)
    return sqlite, (statementsets, tables, views)
