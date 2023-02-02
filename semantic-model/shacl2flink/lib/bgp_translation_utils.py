#
# Copyright (c) 2022, 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import sys
import os
import re
import random
from rdflib import Namespace, URIRef, Variable, BNode, Literal
from rdflib.namespace import RDF, RDFS
import copy


class WrongSparqlStructure(Exception):
    pass


class SparqlValidationFailed(Exception):
    pass


basequery = """
PREFIX iff: <https://industry-fusion.com/types/v0.9/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
SELECT DISTINCT
"""

ngsild = Namespace("https://uri.etsi.org/ngsi-ld/")

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
import utils  # noqa: E402
import configs  # noqa: E402


def create_varname(variable):
    """
    creates a plain varname from RDF varialbe
    e.g. ?var => var
    """
    return variable.toPython()[1:]


def isentity(ctx, variable):
    if create_varname(variable) in ctx['bounds']:
        table = ctx['bounds'][create_varname(variable)]
    else:
        return False
    if re.search(r'\.id$', table):
        return True
    else:
        return False


def create_tablename(subject, predicate='', namespace_manager=None):
    """
    Creates a sql tablename from an RDF Varialbe.
    e.g. ?var => VARTABLE
    variable: RDF.Variable or RDF.URIRef
    """
    pred = predicate
    subj = ''
    if pred != '' and namespace_manager is not None:
        pred = namespace_manager.compute_qname(predicate)[2]
        pred = pred.upper()
    if isinstance(subject, Variable):
        subj = subject.toPython().upper()[1:]
    elif isinstance(subject, URIRef) and namespace_manager is not None:
        subj = namespace_manager.compute_qname(subject)[2]
        subj = subj.upper()
    else:
        raise SparqlValidationFailed(f'Could not convert subject {subject} to \
table-name')

    return f'{subj}{pred}TABLE'


def merge_where_expression(where1, where2):
    if where1 == '' and where2 == '':
        return ''
    elif where1 == '':
        return where2
    elif where2 == '':
        return where1
    else:
        return f'{where1} and {where2}'


def get_rdf_join_condition(r, property_variables, entity_variables,
                           selectvars):
    """
    Create join condition for RDF-term
    e.g. ?table => table.id

    r: RDF term
    property_variables: List of variables containing property values
    entity_variables: List of variables containing entity references
    selectvars: mapping of resolved variables
    """
    if isinstance(r, Variable):
        var = create_varname(r)
        if r in property_variables:
            if var in selectvars:
                return selectvars[var]
            else:
                raise SparqlValidationFailed(f'Could not resolve variable \
?{var} at this point. You might want to rearrange the query to hint to \
translator.')
        elif r in entity_variables:
            raise SparqlValidationFailed(f'Cannot bind enttiy variable {r} to \
plain RDF context')
        elif var in selectvars:  # plain RDF variable
            return selectvars[var]
    elif isinstance(r, URIRef) or isinstance(r, Literal):
        return f'\'{utils.format_node_type(r)}\''
    else:
        raise SparqlValidationFailed(f'RDF term {r} must either be a Variable, \
IRI or Literal.')


def sort_triples(ctx, bounds, triples, graph):
    """Sort a BGP according to dependencies. Externally dependent triples come
    first

    Sort triples with respect to already bound variables
    try to move triples without any bound variable to the end

    Args:
    bounds (dictionary): already bound variables
    triples (dictionary): triples to be sorted
    graph (RDFlib Graph): graph containing the same triples as 'triples' but
    searchable with RDFlib
    """
    def select_candidates(bounds, triples, graph):
        for s, p, o in triples:
            count = 0
            # look for nodes: (1) NGSI-LD node and (2) plain RDF (3) RDF type definition (4) rest
            if isinstance(s, Variable) and (p.toPython() in ctx['relationships'] or
                                            p.toPython() in ctx['properties']):
                if isinstance(o, BNode):
                    blanktriples = graph.triples((o, None, None))
                    for (bs, bp, bo) in blanktriples:
                        # (1)
                        if create_varname(s) in bounds:
                            count += 1
                            if isinstance(bo, Variable):
                                bounds[create_varname(bo)] = ''
                        elif isinstance(bo, Variable) and create_varname(bo)\
                                in bounds:
                            count += 1
                            bounds[create_varname(s)] = ''
                        elif isinstance(bo, URIRef) or isinstance(bo, Literal):
                            raise SparqlValidationFailed(f'Tried to bind {s}\
to Literal or IRI instead of Variable. Not implemented. Workaround to bind {s}\
to Variable and use FILTER.')
            elif isinstance(s, Variable) and p == RDF['type']:
                # (3)
                # definition means s is variable and p is <a>
                # when ?o is IRI then add ?s
                # when ?o is varible and ?s is bound, then define ?o
                if isinstance(o, URIRef):
                    count += 1
                    if create_varname(s) not in bounds:
                        bounds[create_varname(s)] = ''
                elif isinstance(o, Variable) and create_varname(s) in bounds:
                    count += 1
                    bounds[create_varname(o)] = ''
            elif not isinstance(s, BNode) or (p != ngsild['hasValue'] and p !=
                                              ngsild['hasObject'] and p != RDF['type']):  # (2)
                if isinstance(s, Variable) and create_varname(s) in bounds and not isinstance(o, BNode):
                    count += 1
                    if isinstance(o, Variable):
                        bounds[create_varname(o)] = ''
                elif isinstance(o, Variable) and create_varname(o) in bounds:
                    count += 1
                    if isinstance(s, Variable):
                        bounds[create_varname(s)] = ''
                elif isinstance(o, BNode):  # rdf with blank nodes
                    blanktriples = graph.triples((o, None, None))
                    for (bs, bp, bo) in blanktriples:
                        if create_varname(s) in bounds:
                            count += 1
                            if isinstance(bo, Variable):
                                bounds[create_varname(bo)]
                        elif isinstance(bo, Variable) and create_varname(bo) in bounds:
                            count += 1
                            bounds[create_varname(s)] = ''
            elif isinstance(s, BNode):
                #  (4)
                count = 1
            else:
                raise SparqlValidationFailed("Could not reorder BGP triples.")
            if count > 0:
                return (s, p, o)

    bounds = copy.deepcopy(bounds)  # do not change the "real" bounds
    result = []
    while len(triples) > 0:
        candidate = select_candidates(bounds, triples, graph)
        if candidate is None:
            raise SparqlValidationFailed("Could not determine the right order \
of triples")
        result.append(candidate)
        triples.remove(candidate)

    return result


def get_random_string(num):
    return ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(num))


def create_ngsild_mappings(ctx, sorted_graph):
    """Create structure which help to detect property/relationship variables
        
        We have to treat property and entity variables different
        since these are stored in different tables compared to
        plain RDF.
        entity variable is before a ngsild:property or ngsild:relationship (as defined in shacl.ttl by sh:property) or
        after iff:hasObject as Relationship.
        property_variable is after ngsild:hasValue
        Example BGP:
        BNode('Nc26056f5cd4647b697135d4a71ebc35a') <https://uri.etsi.org/ngsi-ld/hasObject> ?f .
        ?f <https://industry-fusion.com/types/v0.9/state> BNode('N4268834d83074ba1a14c199b3d6de955') .
        ?this <https://industry-fusion.com/types/v0.9/hasFilter> BNode('Nc26056f5cd4647b697135d4a71ebc35a') .
        ?this <'https://industry-fusion.com/types/v0.9/state'> BNode('Nd6d77ea8f25945c58c9ff19c8f853094') .
        BNode('N4268834d83074ba1a14c199b3d6de955') <'https://uri.etsi.org/ngsi-ld/hasValue'> ?v2 .
        BNode('Nd6d77ea8f25945c58c9ff19c8f853094') <'https://uri.etsi.org/ngsi-ld/hasValue> ?v1 .
        Would lead to:
        property_variables = {"v2": True, "v1": True}
        entity_variables = {"f": True, "this": True}
        row = {"f": "https://industry-fusion.com/types/v0.9/filter", "this": "https://industry-fusion.com/types/v0.9/cutter",
               "v1": "https://industry-fusion.com/types/v0.9/cutter", "v2": "https://industry-fusion.com/types/v0.9/filter"}

    Args:
        ctx (dictionary): sparql context containing metadata and results
        sorted_graph (dictionary): triples from bgp with defined order
    Returns:
        Touple of Property_variables, entity_variables, row dictionaries containing the respective
        predicates and mapping
    """  # noqa E501

    property_variables = {}
    entity_variables = {}
    for s, p, o in sorted_graph:
        if p == ngsild['hasValue']:
            if isinstance(o, Variable):
                property_variables[o] = True
        if p == ngsild['hasObject']:
            if isinstance(o, Variable):
                entity_variables[o] = True
        if p.toPython() in ctx['relationships']:
            if isinstance(s, Variable):
                entity_variables[s] = True
        if p.toPython() in ctx['properties']:
            if isinstance(s, Variable):
                entity_variables[s] = True
    # For every entity or property_variable, find out to which entity class it belongs to.
    # Straight forward way is to create another sparql query against shacl.ttl to validate
    # that varialbles have a meaningful target.
    # It is okay to have ambiguities but if there is no result an exception is thrown, because this query
    # cannot lead to a result at all.
    if property_variables or entity_variables:

        sparqlvalidationquery = ''
        equivalence = []
        variables = []
        for key, value in ctx['classes'].items():
            sparqlvalidationquery += f'?{key} rdfs:subClassOf <{value.toPython()}> .\n'
            sparqlvalidationquery += f'<{value.toPython()}> rdfs:subClassOf ?{key} .\n'
        for entity in entity_variables.keys():
            sparqlvalidationquery += f'?{entity}shape sh:targetClass ?{entity} .\n'
            variables.append(entity)
            for s, p, o in sorted_graph.triples((entity, None, None)):
                property_class = sorted_graph.value(o, ngsild['hasObject'])
                if property_class is not None:
                    sparqlvalidationquery += f'?{s}shape sh:property [ sh:path <{p}> ; sh:property \
[ sh:path ngsild:hasObject;  sh:class ?{property_class} ] ] .\n'
        for property in property_variables:
            variables.append(property)
            sparqlvalidationquery += f'?{property}shape sh:targetClass ?{property} .\n'
            for s, p, o in sorted_graph.triples((None, ngsild['hasValue'], property)):
                for p in sorted_graph.predicates(object=s):
                    sparqlvalidationquery += f'?{property}shape sh:property [ sh:path <{p}> ; ] .\n'
                    for subj in sorted_graph.subjects(predicate=p, object=s):
                        if isinstance(subj, Variable):
                            equivalence.append(f'{subj.toPython()}shape = ?{property}shape')
        query = basequery
        for variable in variables:
            query += f'?{variable} '
        query += '\nwhere {\n' + sparqlvalidationquery
        first = True
        for equiv in equivalence:
            if first:
                first = False
                query += 'filter('
            else:
                query += ' && '
            query += equiv
        if not first:
            query += ')\n}'
        else:
            query += '}'

        # Now execute the validation query
        # For the time being only unique resolutions of classes are allowed.
        # TODO: Implement multi class resolutions
        qres = ctx['g'].query(query)
        if len(qres) != 1:
            raise SparqlValidationFailed("Validation of BGP failed. It either contradicts what is defined in \
SHACL or is too ambigue!")
    else:
        # no ngsi-ld variables found, so do not try to infer the types
        qres = []

    row = None
    for r in qres:
        row = r
    return property_variables, entity_variables, row


def process_ngsild_spo(ctx, local_ctx, s, p, o):
    """Processes triple which relates to NGSI-LD objects

    Typical NGSI-LD reference in SPARQL looks like this:
    ?id p [hasValue|hasObject ?var|iri|literal]
    id is id of NGSI-LD object
    p is predicate of NGSI-LD as defined in SHACL
    hasValue|hasObject dependent on whether p describes a property or a relationship
    var|uri either binds var to the pattern or a concrete literal|iri

    case 1: hasValue + ?var, ?id already bound
    select idptable.hasValue from attribues as idptable where idptable.id = idtable.p
    case 2: hasObject + ?var, ?id already bound(known)
    if ?id is bound and ?var is not bound and hasObject attribute is used:
    The p-attribute is looked up in the attributes table and the ?var-id is looked up in the respective
    type[?var] table. e.g. ?id p [hasObject ?var] =>
        Select * from attributes as idptable join type[?var] as vartable where idptable.id = idtable.p and idptable.hasObject = vartable.id
    case 3: hasObject + ?var, ?id is not bound(known) but ?var is known
        Select * from type[?id] as idtable join attributes as idptable where idtable.p = idptable.id  and idptable.hasObject = vartable.id

    Args:
        ctx (dictionary): RDFlib context from SPARQL parser
        local_ctx (dictionary): local context only relevant for current BGP
        s (RDFlib term): subject
        p (RDFLib term): predicate
        o (RDFLib term): object

    Raises:
        SparqlValidationFailed: limitation in SPARQL translation implementation
    """ # noqa E501

    # We got a triple <?var, p, []> where p is a shacle specified property
    # Now we need the ngsild part to determine if it is a relationship or not
    ngsildtype = list(local_ctx['h'].predicates(subject=o))
    ngsildvar = list(local_ctx['h'].objects(subject=o))
    if len(ngsildtype) != 1 or len(ngsildvar) != 1:
        raise SparqlValidationFailed(f'No matching ngsiltype or ngsildvar found for variable {s.toPython()}')
    if not isinstance(ngsildvar[0], Variable):
        raise SparqlValidationFailed(f'Binding of {s} to concrete iri|literal not (yet) supported. \
Consider to use a variable and FILTER.')
    # Now we have 3 parts:
    # ?subject_var p [ hasValue|hasObject ?object_var]
    # subject_table, attribute_table, object_table
    subject_tablename = f'{s.toPython().upper()}TABLE'[1:]
    subject_varname = f'{s.toPython()}'[1:]
    subject_sqltable = utils.camelcase_to_snake_case(utils.strip_class(local_ctx['row'][subject_varname]))
    attribute_sqltable = utils.camelcase_to_snake_case(utils.strip_class(p))
    attribute_tablename = f'{subject_varname.upper()}{attribute_sqltable.upper()}TABLE'
    # In case of Properties, no additional tables are defined
    if ngsildtype[0] == ngsild['hasValue']:
        if create_varname(ngsildvar[0]) not in local_ctx['bounds']:
        #    local_ctx['selvars'][ngsildvar[0].toPython()[1:]] = f'`{attribute_tablename}`.`{ngsildtype[0]}`'
            local_ctx['bounds'][ngsildvar[0].toPython()[1:]] = f'`{attribute_tablename}`.`{ngsildtype[0]}`'
        join_condition = f'{attribute_tablename}.id = {subject_tablename}.`{p}`'
        sql_expression = f'attributes_view AS {attribute_tablename}'
        local_ctx['bgp_tables'][attribute_tablename] = []
        local_ctx['bgp_sql_expression'].append({'statement': f'{sql_expression}',
                                                'join_condition': f'{join_condition}'})
    else:
        # In case of Relationships there are two cases:
        # (1) object_var is not defined
        # (2) object_var is already definied but no subject_var
        if ngsildtype[0] != ngsild['hasObject']:
            raise SparqlValidationFailed("Internal implementation error")
        if not isinstance(ngsildvar[0], Variable):
            raise SparqlValidationFailed(f'Binding {s} to non-variable {ngsildvar[0]} not supported. \
Consider using a variable and FILTER instead.')
        object_varname = f'{ngsildvar[0].toPython()}'[1:]
        object_sqltable = utils.camelcase_to_snake_case(utils.strip_class(local_ctx['row'][object_varname]))
        object_tablename = f'{object_varname.upper()}TABLE'
        if object_varname not in local_ctx['bounds']:
            # case (1)
            join_condition = f'{attribute_tablename}.id = {subject_tablename}.`{p}`'
            sql_expression = f'attributes_view AS {attribute_tablename}'
            local_ctx['bgp_tables'][attribute_tablename] = []
            local_ctx['bgp_tables'][object_tablename] = []
            local_ctx['bgp_sql_expression'].append({'statement': f'{sql_expression}',
                                                    'join_condition': f'{join_condition}'})
            local_ctx['bgp_sql_expression'].append({'statement': f'{object_sqltable}_view AS {object_tablename}',
                                                    'join_condition': f'{object_tablename}.id = \
{attribute_tablename}.`{ngsildtype[0].toPython()}`'})
            ctx['sql_tables'].append(object_sqltable)
            # if object_varname not in local_ctx['bounds']:
            #local_ctx['selvars'][object_varname] = f'{object_tablename}.`id`'
            local_ctx['bounds'][object_varname] = f'{object_tablename}.`id`'
        else:
            # case (2)
            join_condition = f'{attribute_tablename}.`{ngsildtype[0].toPython()}` = {object_tablename}.id'
            sql_expression = f'attributes_view AS {attribute_tablename}'
            local_ctx['bgp_sql_expression'].append({'statement': f'{sql_expression}',
                                                    'join_condition': f'{join_condition}'})
            join_condition = f'{attribute_tablename}.id = {subject_tablename}.`{p}`'
            sql_expression = f'{subject_sqltable}_view AS {subject_tablename}'
            ctx['sql_tables'].append(subject_sqltable)
            local_ctx['bgp_tables'][attribute_tablename] = []
            local_ctx['bgp_tables'][subject_tablename] = []
            local_ctx['bgp_sql_expression'].append({'statement': f'{sql_expression}',
                                                   'join_condition': f'{join_condition}'})
            if subject_varname not in local_ctx['bounds']:
                #local_ctx['selvars'][subject_varname] = f'`{subject_tablename}`.`id`'
                local_ctx['bounds'][subject_varname] = f'`{subject_tablename}`.`id`'


def process_rdf_spo(ctx, local_ctx, s, p, o):
    """Processes a subject, predicate, object triple and create sql term for it
    
    This processing assumes that the triple contains no ngsi-ld related term (such as hasObject, hasValue) and is a pure RDF triple
    Note that there cannot be arbitrate RDF terms. In our framework, the RDF(knowledge) is immutable. Everything which
    can change must be an NGSI-LD object(model). Therefore, for instance, there cannot be a term like:
    <ngsild-id> <pred> <object>
    because <pred> cannot be a defined NGSI-LD property/relationship (otherwise it would not be processed here)
    A "generic" relationship between knowledge and model is impossible then (because it would be either a NGSI-LD defined relation or
    the immutable knowledge must reference id's of the (mutable) model which is not possible by definition)

    Args:
        ctx (dictionary): global context derived from RDFlib SPARQL parser
        local_ctx (dictionary): local context only relevant for the BGP processing
        s (RDFLib term): subject
        p (RDFLib term): predicate
        o (RDFLib term): object

    Raises:
        SparqlValidationFailed: Reports implementation limitations
    """ # noqa E501
    # must be  RDF query
    if not isinstance(p, URIRef):
        raise SparqlValidationFailed("NON IRI RDF-predicate not (yet) supported.")
    if isinstance(s, BNode):  # Blank node subject, e.g. ([], p, o) is handled by respective (s, p2, []) nodes
        return
    # predicate must be static for now
    # NGSI-LD entity variables cannot be referenced in plain RDF with one exception:
    # ?var a ?type is allowed an the only connection between the knowledge and the model
    # if a new variable is found, which is neither property, nor entity, it will be bound
    # by RDF query
    rdftable_name = create_tablename(s, p, ctx['namespace_manager']) + get_random_string(10)

    # Process Subject.
    # If subject is variable AND NGSI-LD Entity, there is a few special cases which are allowed.
    # e.g. ?var a ?type
    # e.g. ?var a <iri>/Literal
    # relationship between NGSI-LD Entity subject and RDF term is otherwise forbidden
    subject_join_condition = None
    if isinstance(s, Variable) and (s in local_ctx['entity_variables'] or isentity(ctx, s)):
        # special case p == rdf-type
        if p == RDF['type']:
            entity = local_ctx['bounds'].get(create_varname(s))
            if entity is None and isinstance(o, URIRef):  # create entity table based on type definition
                subject_tablename = f'{s.toPython().upper()}TABLE'[1:]
                subject_varname = f'{s.toPython()}'[1:]
                subject_sqltable = utils.camelcase_to_snake_case(utils.strip_class(local_ctx['row'][subject_varname]))
                local_ctx['bgp_sql_expression'].append({'statement': f'{subject_sqltable}_view AS {subject_tablename}',
                                                        'join_condition': ''})
                ctx['sql_tables'].append(subject_sqltable)
                #local_ctx['selvars'][subject_varname] = f'{subject_tablename}.`id`'
                local_ctx['bounds'][subject_varname] = f'{subject_tablename}.`id`'
                local_ctx['bgp_tables'][subject_tablename] = []
                predicate_join_condition = f"{rdftable_name}.predicate = '" + RDFS['subClassOf'].toPython() + "'"
                object_join_condition = f"{rdftable_name}.object = '{o.toPython()}'"
                subject_join_condition = f"{rdftable_name}.subject = {subject_tablename}.`type`"
                join_condition = f"{subject_join_condition} and {predicate_join_condition} and {object_join_condition}"
                statement = f"{configs.rdf_table_name} as {rdftable_name}"
                local_ctx['bgp_sql_expression'].append({'statement': statement, 'join_condition': join_condition})
                return
            else:
                entity = entity.replace('.`id`', '.id')  # Normalize cases when id is quoted
                entity_table = entity.replace('.id', '')
                entity_column = entity.replace('.id', '.type')
                global_tables = ctx['tables']
                if entity_table not in global_tables:
                    global_tables[entity_table] = []
                global_tables[entity_table].append('type')
                if isinstance(o, Variable):
                    # OK let's process the special case here
                    # Two cases: (1) object variable is bound (2) object variable unknown

                    object_join_bound = get_rdf_join_condition(o, local_ctx['property_variables'],
                                                               local_ctx['entity_variables'], local_ctx['bounds'])
                    if object_join_bound is None:
                        # (2)
                        # bind variable with type column of subject
                        # add variable to local table
                        #local_ctx['selvars'][create_varname(o)] = entity_column
                        local_ctx['bounds'][create_varname(o)] = entity_column
                        return
                    else:
                        # (1)
                        # variable is bound, so get it and link it with bound value
                        objvar = local_ctx['bounds'][create_varname(o)]
                        local_ctx['where'] = merge_where_expression(local_ctx['where'], f'{entity_column} = {objvar}')
                        return
                else:
                    # subject entity variable but object is no variable
                    local_ctx['where'] = merge_where_expression(local_ctx['where'],
                                                                f'{entity_column} = \'{utils.format_node_type(o)}\'')
                    return
        else:
            raise SparqlValidationFailed("Cannot query generic RDF term with NGSI-LD entity subject.")
    else:
        # No special case. Check if subject is non bound and if non bound whether it can be bound
        subject_join_bound = get_rdf_join_condition(s, local_ctx['property_variables'],
                                                    local_ctx['entity_variables'], local_ctx['bounds'])
        if subject_join_bound is None:
            if not isinstance(s, Variable):
                raise SparqlValidationFailed("Could not resolve {s} and not a variable")
            # Variable not found, needs to be added
            subj_column = f'`{rdftable_name}`.`subject`'
            #local_ctx['selvars'][create_varname(s)] = subj_column
            local_ctx['bounds'][create_varname(s)] = subj_column
            subject_join_bound = None
        subject_join_condition = f'{rdftable_name}.subject = {subject_join_bound}'\
            if subject_join_bound is not None else None
    predicate_join_condition = f'{rdftable_name}.predicate = \'{utils.format_node_type(p)}\''
    # Process object join condition
    # object variables which are referencing ngsild-entities are forbidden
    if isinstance(o, Variable) and o in local_ctx['entity_variables']:
        raise SparqlValidationFailed('Cannot bind NGSI-LD Entities to RDF objects.')
    # two cases: (1) object is either variable or Literal/IRI (2) object is Blank Node
    if not isinstance(o, BNode):  # (1)
        object_join_bound = get_rdf_join_condition(o, local_ctx['property_variables'],
                                                   local_ctx['entity_variables'], local_ctx['bounds'])
        if object_join_bound is None:
            if not isinstance(o, Variable):
                raise SparqlValidationFailed("Could not resolve {o} not being a variable")
            # Variable not found, needs to be added
            #local_ctx['selvars'][create_varname(o)] = f'{rdftable_name}.object'
            local_ctx['bounds'][create_varname(o)] = f'{rdftable_name}.object'
            object_join_bound = None
        object_join_condition = f'{rdftable_name}.object = {object_join_bound}' \
            if object_join_bound is not None else None
        join_condition = f'{predicate_join_condition}'
        # if we found join condition for subject and object, add them
        if subject_join_condition is not None:
            join_condition = f'{subject_join_condition} and {join_condition}'
        if object_join_condition is not None:
            join_condition += f' and {object_join_condition}'
        sql_expression = f'{configs.rdf_table_name} AS {rdftable_name}'
        local_ctx['bgp_tables'][rdftable_name] = []
        local_ctx['bgp_sql_expression'].append({'statement': f'{sql_expression}',
                                                'join_condition': f'{join_condition}'})
    else:  # (2)
        # We need to translate (s, p1, []), ([], p2, o) which means to join two tables
        # rdf as table1 on table1.predicate = p1 (and table1.subject = cond1) and table1.object = BN join
        # rdf as table2 on table2.predicate = p2 (and table2.object = cond2) and table2.subject = table1.object
        # (no need to check table2.subject = BN)
        sql_expression = f'{configs.rdf_table_name} AS {rdftable_name}'
        blankjoincondition = f'{rdftable_name}.object LIKE \'_:%\''
        join_condition = f'{predicate_join_condition} and {blankjoincondition}'
        if subject_join_condition is not None:
            join_condition = f'{subject_join_condition} and {join_condition}'
        local_ctx['bgp_tables'][rdftable_name] = []
        local_ctx['bgp_sql_expression'].append({'statement': f'{sql_expression}',
                                                'join_condition': f'{join_condition}'})

        for (bs, bp, bo) in local_ctx['h'].triples((o, None, None)):
            bo_rdftable_name = create_tablename(bo, bp, ctx['namespace_manager']) + get_random_string(10)
            bo_predicate_join_condition = f'{bo_rdftable_name}.predicate = \'{utils.format_node_type(bp)}\' and \
                {rdftable_name}.object = {bo_rdftable_name}.subject'
            object_join_bound = get_rdf_join_condition(bo, local_ctx['property_variables'],
                                                       local_ctx['entity_variables'], local_ctx['bounds'])
            if object_join_bound is None:
                if not isinstance(bo, Variable):
                    raise SparqlValidationFailed("Could not resolve {bo} not being a variable")
                # Variable not found, needs to be added
                #local_ctx['selvars'][create_varname(bo)] = f'{bo_rdftable_name}.object'
                local_ctx['bounds'][create_varname(bo)] = f'{bo_rdftable_name}.object'
                object_join_bound = None
            object_join_condition = f'{bo_rdftable_name}.object = {object_join_bound}' \
                if object_join_bound is not None else None
            join_condition = f'{bo_predicate_join_condition}'
            # if we found join condition for subject and object, add them
            if subject_join_condition is not None:
                join_condition = f'{subject_join_condition} and {join_condition}'
            if object_join_condition is not None:
                join_condition += f' and {object_join_condition}'
            sql_expression = f'{configs.rdf_table_name} AS {bo_rdftable_name}'
            local_ctx['bgp_tables'][bo_rdftable_name] = []
            local_ctx['bgp_sql_expression'].append({'statement': f'{sql_expression}',
                                                    'join_condition': f'{join_condition}'})