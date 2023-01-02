# from msilib.schema import tables
import sys
import os
import re
import random
from rdflib import Graph, Namespace, URIRef, Variable, BNode, Literal
from rdflib.namespace import RDF
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.algebra import translateQuery
import owlrl
import copy

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
import utils  # noqa: E402
import configs  # noqa: E402


class WrongSparqlStructure(Exception):
    pass


class SparqlValidationFailed(Exception):
    pass


sh = Namespace("http://www.w3.org/ns/shacl#")
ngsild = Namespace("https://uri.etsi.org/ngsi-ld/")
iff = Namespace("https://industry-fusion.com/types/v0.9/")
debug = 0
debugoutput = sys.stdout
dummyvar = 'dummyvar'


sparql_get_properties = """
PREFIX iff: <https://industry-fusion.com/types/v0.9/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
SELECT 
    ?targetclass ?property
where {
    ?nodeshape a sh:NodeShape .
    ?nodeshape sh:targetClass ?targetclass .
    ?nodeshape sh:property [ 
        sh:path ?property ; 
        sh:property [
            sh:path ngsild:hasValue ;
        ] ;

    ] .
}

"""

sparql_get_relationships = """
PREFIX iff: <https://industry-fusion.com/types/v0.9/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
SELECT 
    ?targetclass ?relationship
where {
    ?nodeshape a sh:NodeShape .
    ?nodeshape sh:targetClass ?targetclass .
    ?nodeshape sh:property [ 
        sh:path ?relationship ; 
        sh:property [
            sh:path ngsild:hasObject ;
        ] ;

    ] .
}

"""

basequery = """
PREFIX iff: <https://industry-fusion.com/types/v0.9/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ngsild: <https://uri.etsi.org/ngsi-ld/>
PREFIX sh: <http://www.w3.org/ns/shacl#>
SELECT DISTINCT
"""

properties = {}
relationships = {}
g = Graph()


def translate_sparql(shaclfile, knowledgefile, sparql_query, target_class):
    """
    Translates shaclfile + knowledgefile into SQL instructions

    Parameters:
        shaclfile (string)    : filename of shacl file
        knowledgefile (string): filename of knowledge file
        sparql_query (string) : query as string
        target_class          : class of the `this` variable

    Returns:
        sql_term (string)
        used sql-tables (dict[string])
    """
    global g
    global properties
    global relationships
    g.parse(shaclfile)
    h = Graph()
    h.parse(knowledgefile)
    g += h
    rdfs = owlrl.RDFSClosure.RDFS_Semantics(g, axioms=True, daxioms=False, rdfs=True).closure()
    sh = Namespace("http://www.w3.org/ns/shacl#")
    ngsild = Namespace("https://uri.etsi.org/ngsi-ld/")
    iff = Namespace("https://industry-fusion.com/types/v0.9/")

    qres = g.query(sparql_get_properties)
    for row in qres:
        if row.property is not None:
            properties[row.property.toPython()] = True

    qres = g.query(sparql_get_relationships)
    for row in qres:
        if row.relationship is not None:
            relationships[row.relationship.toPython()] = True
    parsed_query = translateQuery(parseQuery(sparql_query))
    ctx = translate_query(parsed_query, target_class)
    return ctx['target_sql'], ctx['sql_tables']

def create_tablename(subject, predicate = '', namespace_manager = None):
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
        raise SparqlValidationFailed(f'Could not convert subject {subject} to table-name')

    return f'{subj}{pred}TABLE'


def create_varname(variable):
    """
    creates a plain varname from RDF varialbe
    e.g. ?var => var 
    """
    return variable.toPython()[1:]


def get_rdf_join_condition(r, property_variables, entity_variables, selectvars):
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
                raise SparqlValidationFailed(f'Could not resolve variable ?{var} at this point. You might want to rearrange the query to hint to translator.')
        elif r in entity_variables:
            raise SparqlValidationFailed(f'Cannot bind enttiy variable {r} to plain RDF context')
        #    if var in selectvars:
        #        return f'{create_tablename(r)}.id'
        elif var in selectvars: # plain RDF variable
            return selectvars[var]
        #else:
        #    raise SparqlValidationFailed(f'Could not resolve varialbe {r}')
    elif isinstance(r, URIRef) or isinstance(r, Literal):
        return f'\'{r.toPython()}\''
    else:
        raise SparqlValidationFailed(f'RDF term {r} must either be a Variable, IRI or Literal.')
    

def create_bgp_context(bounds, join_conditions, sql_expression, tables):
    return {
        'bounds': bounds,
        'join_conditions': join_conditions,
        'sql_expression': sql_expression,
        'tables': tables
    }

def translate_query(query, target_class):
    """
    Decomposes parsed SparQL object
    query: parsed sparql object
    """
    algebra = query.algebra
    ctx = {'namespace_manager': query.prologue.namespace_manager, 
            'PV': algebra.PV,
            'pass': 0,
            'target_used': False,
            'table_id': 0,
            'classes': {'this': target_class},
            'sql_tables': [utils.camelcase_to_snake_case(utils.strip_class(target_class)), 'attributes'],
            'bounds': {'this': 'THISTABLE.id'},
            'tables': {'THISTABLE': ['id']},
            'target_sql': '',
            'target_where': '',
            'target_modifiers': [],
            'target_ctx': create_bgp_context({'this': 'THISTABLE.id'}, 
                                                [],
                                                [{'statement': f'{ utils.camelcase_to_snake_case(utils.strip_class(target_class))}_view as THISTABLE',
                                                'join_condition': ''}], 
                                                ['THISTABLE']
                                            )
    }
    #ctx["tables"] = {'THISTABLE': ctx["target_ctx"]}
    if debug: print("DEBUG: First Pass.", file=debugoutput)
    if algebra.name == 'SelectQuery':
        translate(ctx, algebra)
    else:
        raise WrongSparqlStructure('Only SelectQueries are supported currently!')
    
    if debug: print("DEBUG: Second Pass.", file=debugoutput)
    ctx['pass'] = 1
    translate(ctx,algebra)
    if debug: print('DEBUG: Result: ', ctx['target_sql'], file=debugoutput)
    return ctx

def translate(ctx, elem):
    """
    Translate all objects
    """
    if elem.name == 'SelectQuery':
        return translate_select_query(ctx, elem)
    elif elem.name == 'Project':
        result = translate_project(ctx, elem)
        return result
    elif elem.name == 'Filter':
        if ctx['pass'] == 0:
            translate_filter(ctx, elem)
        #else:
            #return construct_sql(ctx, elem)
    elif elem.name == 'BGP':
        if ctx['pass'] == 0:
            translate_BGP(ctx, elem)
        else:
            select = False
            if ctx['target_sql'] == '':
                select = True
            if 'sql_expression' in elem['sql_context']:
                result, where = merge_bgp_context(elem['sql_context']['sql_expression'], select)
                ctx['target_sql'] = ctx['target_sql'] + result
                merge_where_context(ctx, where)
    elif elem.name == 'ConditionalAndExpression':
        result = translate_and_expression(ctx, elem)
        return result
    elif elem.name == 'RelationalExpression':
        result = translate_relational_expression(ctx, elem)
        return result
    elif elem.name == 'Join':
        return translate_join(ctx, elem)
    elif elem.name == 'Builtin_NOTEXISTS':
        return translate_notexists(ctx, elem)
    elif elem.name == 'Distinct':
        ctx['target_modifiers'].append('Distinct')
        translate(ctx, elem.p)
    else:
        raise WrongSparqlStructure(f'SparQL structure {elem.name} not supported!')

def translate_select_query(ctx, query):
    """
    Decomposes SelectQuery object
    """
    if debug > 2: print(f'SelectQuery: {query}', file=debugoutput)
    return translate(ctx, query.p)

def translate_project(ctx, project):
    """
    Translate Project structure
    """
    if debug > 2: print(f'DEBUG: Project: {project}', file=debugoutput)
    translate(ctx, project.p)
    if ctx['pass'] == 0:
        add_projection_vars_to_tables(ctx)
    if ctx['pass'] == 1:
        select_expression = ctx['target_sql']
        if select_expression == '':
            select_expression = construct_sql(ctx, project.p)
        if not ctx['target_used'] and ctx['target_ctx'] != None:
            ctx['target_used'] = True
            # special case: first join condition
            prefix, where = merge_bgp_context(ctx['target_ctx']['sql_expression'], True)
            if where != '':
                raise WrongSparqlStructure("Where condition found but not used.")
            select_expression = f'{prefix} JOIN {select_expression}'
                #prefix = construct_sql(ctx, project.p)
            #select_expression_pre = create_join_expressions(ctx, ctx['target_sql'], ctx['target_ctx'])
            #select_expression = f'{select_expression_pre} JOIN {select_expression}'
        ctx['target_sql'] = select_expression
        wrap_sql_projection(ctx)

def add_projection_vars_to_tables(ctx):
    bounds = ctx['bounds']
    for var in ctx['PV']:
        try:
            column = bounds[create_varname(var)]
            column_no_bacticks =  column.replace('`', '')
            table_name, column = re.findall('^([A-Z0-9_]+)\.(.*)$', column_no_bacticks)[0]
            if table_name not in ctx['tables']:
                ctx['tables'][table_name] = [f'{column}']
            else:
                ctx['tables'][table_name].append(f'{column}')
            #expression += f'`{column_no_bacticks}` AS `{create_varname(var)}` '
        except:
            pass # variable cannot mapped to a table, ignore it


def wrap_sql_projection(ctx):
    bounds = ctx['bounds']
    expression = 'SELECT '
    if 'Distinct' in ctx['target_modifiers']:
        expression += 'DISTINCT '
    if len(ctx['PV']) == 0:
        raise SparqlValidationFailed("No Projection variables given.")

    first = True
    for var in ctx['PV']:
        if first:
            first = False
        else:
            expression += ', '
        try:
            column = bounds[create_varname(var)]
            # column_no_bacticks =  column.replace('`', '')
            expression += f'{column} AS `{create_varname(var)}` '
        except:
            # variable could not be bound, bind it with NULL
            expression += f'NULL AS `{create_varname(var)}`'

    target_sql = ctx['target_sql']
    target_where = ctx['target_where']
    ctx['target_sql'] = f'{expression} FROM {target_sql}'
    ctx['target_sql'] = ctx['target_sql'] + f' WHERE {target_where}' if target_where != '' else ctx['target_sql']


def translate_filter(ctx, filter):
    """
    Translates Filter object to SQL
    """
    if debug  > 2: print(f'DEBUG: Filter: {filter}', file=debugoutput)
    translate(ctx, filter.p)
    if ctx['pass'] == 0:
        where = translate(ctx, filter.expr)
        filter['sql_context'] = filter.p['sql_context']
        # merge join condition

        for condition in filter.p['sql_context']['join_conditions']:
            if where != '':
                where += f' and {condition}'
            else:
                where = condition
        filter['sql_context']['where'] = where
    #else:
    #    filter['sql_context'] = filter.p['sql_context']
    #return translate_filter_to_sql(query, where)


def translate_notexists(ctx, notexists):
    """
    Translates a FILTER NOT EXISTS expression
    """
    if debug  > 2: print(f'DEBUG: FILTER NOT EXISTS: {notexists}', file=debugoutput)
    ctx_copy = copy_context(ctx)
    translate(ctx_copy, notexists.graph)
    ctx_copy['pass'] = 1
    translate(ctx_copy, notexists.graph)
    remap_join_constraint_to_where(ctx_copy)
    wrap_sql_projection(ctx_copy)
    merge_contexts(ctx, ctx_copy)
    return f'NOT EXISTS ({ctx_copy["target_sql"]})'


def remap_join_constraint_to_where(ctx):
    """
    Workaround for Flink - currently correlated variables in on condition are not working in not-exists subqueries
    Therefore they are remapped to "where" conditions. This will make the query more inefficient but hopefully it 
    can be reomved once FLINK fixed the issue. This method only works so far for rdf tables.
    """
    pattern1 = '(\S*.subject = \S*) and'
    pattern2 = 'and (\S*.object = \S*)'
    toreplace = ctx['target_sql']
    match1 = re.findall(pattern1, toreplace)
    match2 = re.findall(pattern2, toreplace)
    toreplace = re.sub(pattern1, '', toreplace)
    toreplace = re.sub(pattern2, '', toreplace)
    ctx['target_sql'] = toreplace
    first = False
    if ctx['target_where'] == '':
        first = True
    for match in match1:
        if first:
            ctx['target_where'] = ctx['target_where'] + f'{match}'
            first = False    
        else: 
            ctx['target_where'] = ctx['target_where'] + f' and {match}'
    for match in match2:
        ctx['target_where'] = ctx['target_where'] + f' and {match}'

def merge_contexts(ctx, ctx_copy):
    """
    merge global table from ctx_copy into ctx
    ONLY if table in ctx exists, merge it from ctx_copy
    """
    src_tables = ctx_copy['tables']
    target_tables = ctx['tables']

    for table in src_tables:
        if table in target_tables:
            target_table = target_tables[table]
            src_table = src_tables[table]
            for column in src_table:
                if column not in target_table:
                    target_table.append(column)

def copy_context(ctx):
    ctx_copy = copy.deepcopy(ctx)
    ctx_copy['target_sql'] = ''
    ctx_copy['target_ctx'] = None
    ctx_copy['target_modifiers'] = []
    ctx_copy['sql_tables'] = ctx['sql_tables']
    return ctx_copy

def translate_join(ctx, join):
    if debug  > 2: print(f'DEBUG: JOIN: {join}', file=debugoutput)
    if ctx['pass'] == 0:
        translate(ctx, join.p1)
        translate(ctx, join.p2)
    if ctx['pass'] == 1:
        translate(ctx, join.p1)
        # result1 = ''
        # if 'sql_expression' in join.p1['sql_context'] and join.p1['sql_context']['sql_expression'] == '':
        if ctx['target_sql'] != '':
            ctx['target_sql'] = ctx['target_sql'] + ' JOIN '
        # result2 = construct_sql(ctx, join.p2)

        # ctx['target_sql'] = f'{result1} JOIN {result2} ON {join_'
        translate(ctx, join.p2)
        # join condition - assume that it is not a hierarchical JOIN
        join_condition = ''
        try:
            join_condition = join.p2['sql_context']['join_condition']
        except:
            WrongSparqlStructure('Assumption of "left depth" structure violated. No hiearchical right join elements allowed')
        if ctx['target_sql'] != '' and join_condition != '':
            ctx['target_sql'] = ctx['target_sql'] + f' ON {join_condition}'
        #if not ctx['target_used']:
        #    ctx['target_used'] = True
        #    select_expression = create_select_expression(ctx, ctx['target_ctx'])
        #    res = create_join_expressions(ctx, select_expression, result)
        #    print ('join 2nd pass',  res)

    return 

def create_join_expressions(ctx, bgp_context):
    """
    join two expressions:
    select_expr: an expression which is already a valid sql select expression
    bgp_context: bgp_context expression
    """
    where = ''
    if 'where' in bgp_context:
        merge_where_context(ctx, bgp_context['where'])

    join_name = f'J{ctx["table_id"]}'
    
    
    #expression = f'SELECT {columns} FROM'
    #expression = f' ({join_expr}) as {join_name}' if join_expr != '' else ''
    #ctx['table_id'] += 1
    #globalize_join_condition(bgp_context['sql_expression'], bgp_context['tables'], ctx['tables'], join_name)
    merge, where_add = merge_bgp_context(bgp_context['sql_expression'])
    expression = merge
    where = merge_where_context(ctx, where_add)
     
    for condition in bgp_context['join_conditions']:
        #condition = globalize_condition(condition, bgp_context['tables'], ctx['tables'], join_name)
        if where != '':
            where += f' and {condition}'
        else:
            where = condition
    # where = globalize_condition(where, bgp_context['tables'], ctx['tables'], join_name)
    # merge_where_context(ctx, where)
    #expression += f' WHERE {ctx["where"]}' if where != '' else ''
    return expression


def construct_sql(ctx, elem):
    """
    constructs SQL Query from nodes with BGP_Context
    """
    if not elem['sql_context']:
        return ''
    #select_expression = ''

    select_expression = create_join_expressions(ctx, elem['sql_context'])
    return select_expression


def merge_bgp_context(bgp_context, select = False):
    """
    Iterate through bgp_context and create statement out of it
    Normally, it is created for a join but if select is True, it is creating
    a Select merge
    """
    expression = ''
    where = ''
    first = True
    for expr in bgp_context:
        if first:
            first = False
            if not select:
                expression += f'{expr["statement"]} ON {expr["join_condition"]}'
            else:
                where = expr["join_condition"]
                expression = f'{expr["statement"]}'
        else:
            expression += f' JOIN {expr["statement"]} ON {expr["join_condition"]}'
    return expression, where


def merge_where_context(ctx, where_add):
    ctx['target_where'] = merge_where_expression(ctx['target_where'], where_add)
    return ctx['target_where']

def merge_where_expression(where1, where2):
    if where1 == '' and where2 == '': return ''
    elif where1 == '': return where2
    elif where2 == '': return where1
    else: return f'{where1} and {where2}'

def translate_and_expression(ctx, expr):
    """
    Translates AND expression to SQL
    """
    if debug  > 2: print(f'DEBUG: ConditionalAndExpression: {expr}', file=debugoutput)
    result = translate(ctx, expr.expr)
    for otherexpr in expr.other:
        result += ' and '
        result += translate(ctx, otherexpr)
    return result

def translate_relational_expression(ctx, elem):
    """
    Translates RelationalExpression to SQL
    """
    bounds = ctx['bounds']

    if isinstance(elem.expr, Variable):
        expr = bounds[create_varname(elem.expr)]
    elif isinstance(elem.expr, Literal) or isinstance(eleem.expr, URIRef):
        expr = f'\'{elem.expr.toPython()}\''
    else:
        raise WrongSparqlStructure(f'Expression {elem.expr} not supported!')

    if isinstance(elem.other, Variable):
        other = bounds[create_varname(elem.expr)]
    elif isinstance(elem.other, Literal) or isinstance(elem.other, URIRef):
        other = f'\'{elem.other.toPython()}\''
    else:
        raise WrongSparqlStructure(f'Expression {elem.other} not supported!')
    
    op = elem.op
    if elem.op == '!=': op = '<>'

    return f'{expr} {op} {other}'

def translate_filter_to_sql(query, where):
    
    return f'{query} WHERE {where}'


def create_global_columns(ctx, bgp_context):
    columns = ''
    tables = bgp_context['tables']
    
    first = True
    for table in tables:
        ctx['tables'][table] = list(set(ctx['tables'][table])) # deduplicate

        for column in ctx['tables'][table]:
            if first:
                first = False
            else:
                columns += ','
            columns += f'{table}.`{column}` AS `{table}.{column}`'
    return columns

def create_select_expression(ctx, bgp_context):
    """
    """
    sql_expressions = bgp_context['sql_expression']
    expression = 'SELECT '
    expression += create_global_columns(ctx, bgp_context)
    first = True
    where = ''
    table_term = ''
    for sql_expresion in sql_expressions:
        if first:
            first = False
            if 'join_condition' in sql_expresion:
                where = sql_expresion['join_condition']
            table_term += sql_expresion['statement']
        else:
            join_cond = ''
            if 'join_condition' in sql_expresion:
                join_cond = sql_expresion['join_condition']
            table_term += ' JOIN ' + sql_expresion['statement']
            if join_cond != '':
                table_term += f' ON {join_cond}' 

        #exp = sql_expresion['statement']
    expression += f' FROM {table_term}'
    if where != '':
        expression += f'WHERE {where}' # TODO: Globalize where conditino
    return expression

def get_table_name_from_full(full_name):
    """
    Contains full name e.g "table.column"
    and translates to "table"
    """
    return re.search('^([A-Z0-9_]+)\.', )
    


def map_join_condition(sql_expressions, local_tables, global_tables):
    """
    Map all non-local conditions to global table list for later reference
    """
    for expression in sql_expressions:
        to_match = expression['join_condition']
        num_matches = to_match.count('=')
        pattern = '[\s]*([^\s]+)[\s]*=[\s]*([^\s]+)[\s]*[and]*'*num_matches
        match = re.findall(pattern, to_match)
        for var in match[0]:
            try:
                table_name, column = re.findall('^([A-Z0-9_]+)\.(.*)$', var)[0]
                if table_name not in local_tables:
                    column_no_backticks = column.replace('`','')
                    if table_name not in global_tables:
                        global_tables[table_name] = column_no_backticks
                    else:
                        global_tables[table_name].append(column_no_backticks)
            except: # no column variable
                pass

def globalize_join_condition(sql_expressions, local_tables, global_tables, join_table_name):
    """
    Map all non-local conditions to global table list for later reference
    It searches ONLY for equality conditions e.g. a = b
    (Other conditions are currently not supported by Streaming SQL)
    Transformation looks like follows:
    e.g. MYTABLE.`id` => J1.`MYTABLE.id`
    """
    for expression in sql_expressions:
        expression['join_condition'] = globalize_condition(expression['join_condition'], local_tables, global_tables, join_table_name) 
        #to_match = expression['join_condition']
        #new_condition = ''
        #num_matches = to_match.count('=')
        #pattern = '[\s]*([^\s]+)[\s]*=[\s]*([^\s]+)[\s]*[and]*'*num_matches
        #match = re.findall(pattern, to_match)
        #for var in match[0]:
        #    try:
        #        table_name, column = re.findall('^`?([A-Z0-9_]+)`?\.`?(.*)`?$', var)[0]
        #        if table_name not in local_tables:
        #            column_no_backticks = column.replace('`','')
        #            expression['join_condition'] = re.sub( var, f'{join_table_name}.`{table_name}.{column_no_backticks}`', expression['join_condition'])
        #    except:
        #        pass

def globalize_condition(expression, local_tables, global_tables, join_table_name):
    if expression == '':
        return expression
    to_match = expression
    new_condition = ''
    num_matches = to_match.count('=')
    num_matches += to_match.count('<>')
    num_matches += to_match.count('>=')
    num_matches += to_match.count('<=')
    pattern = '[\s]*([^\s]+)[\s]*[<>=]+[\s]*([^\s]+)[\s]*[and]*'*num_matches
    match = re.findall(pattern, to_match)
    # deduplicate match[0]
    columns = list(set(match[0]))
    for var in columns:
        try:
            table_name, column = re.findall('^`?([A-Z0-9_]+)`?\.`?(.*)`?$', var)[0]
            if table_name not in local_tables:
                column_no_backticks = column.replace('`','')
                expression = re.sub( var, f'{join_table_name}.`{table_name}.{column_no_backticks}`', expression)
        except:
            pass
    return expression

def isentity(ctx, variable):
    if create_varname(variable) in ctx['bounds']: 
        table = ctx['bounds'][create_varname(variable)]
    else:
        return False
    if re.search('\.id$', table):
        return True
    else:
        return False


def sort_triples(bounds, triples, graph):
    """
    Sort triples with respect to already bound variables
    try to move triples without any bound variable to the end
    """
    def select_candidates(bounds, triples, graph):
        #result = []
        for s, p, o in triples:
            count = 0
            # look for nodes: (1) NGSI-LD node and (2) plain RDF (3) rest
            if isinstance(s, Variable) and (p.toPython() in relationships or p.toPython() in properties):
                if isinstance(o, BNode):
                    blanktriples = graph.triples((o, None, None))
                    for (bs, bp, bo) in blanktriples:
                        # (1)
                        if create_varname(s) in bounds:
                            count += 1 
                            if isinstance(bo, Variable): bounds[create_varname(bo)] = ''
                        elif isinstance(bo, Variable) and create_varname(bo) in bounds:
                            count += 1
                            bounds[create_varname(s)] = ''
            elif not isinstance(s, BNode) or ( p != ngsild['hasValue'] and p != ngsild['hasObject'] ):
                if isinstance(s, Variable) and create_varname(s) in bounds:
                    count += 1
                    if isinstance(o, Variable): bounds[create_varname(o)] = ''
                elif isinstance(o, Variable) and create_varname(o) in bounds:
                    count += 1 
                    if isinstance(s, Variable): bounds[create_varname(s)] = ''
            elif isinstance(s, BNode):
                # (3)
                count = 1
            else:
                raise SparqlValidationFailed("Could not reorder BGP triples.")
            if count > 0:
                return(s, p, o)

    bounds = copy.deepcopy(bounds) # do not change the "real" bounds
    result = []
    #iterations = len(triples) * len(triples)
    while len(triples) > 0:
        candidate = select_candidates(bounds, triples, graph)
        if candidate is None:
            raise SparqlValidationFailed("Could not determine the right order of triples")
        result.append(candidate)
        triples.remove(candidate)
        #iterations -= 1
        
    return result

def get_random_string(num):
    return ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(num))


def create_ngsild_mappings(ctx, sorted_graph):
    """Create structure which help to detect property/relationship variables
        
        We have to treat property and entity variables different
        since these are stored in different tables comparaed to
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
    """

    property_variables = {}
    entity_variables = {}
    for s,p,o in sorted_graph:
        if p == ngsild['hasValue']:
            if isinstance(o, Variable):
                property_variables[o] = True
        if p == ngsild['hasObject']:
            if isinstance(o, Variable):
                entity_variables[o] = True
        if p.toPython() in relationships:
            if isinstance(s, Variable):
                entity_variables[s] = True
        if p.toPython() in properties:
            if isinstance(s, Variable):
                entity_variables[s] = True
    # For every entity or property_variable, find out to which entity class it belongs to.
    # Straight forward way is to create another sparql query against shacl.ttl to validate
    # that varialbles have a meaningful target.
    # It is okay to have ambiguities but if there is no result an exception is thrown, because this query
    # cannot lead to a result at all.
    if property_variables or entity_variables: 

        sparqlvalidationquery = ''
        equivalence =  []
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
                    sparqlvalidationquery += f'?{s}shape sh:property [ sh:path <{p}> ; sh:property [ sh:path ngsild:hasObject;  sh:class ?{property_class} ] ] .\n'
        for property in property_variables:
            variables.append(property)
            sparqlvalidationquery += f'?{property}shape sh:targetClass ?{property} .\n'
            for s, p, o in sorted_graph.triples((None, ngsild['hasValue'], property)):
                for p in sorted_graph.predicates(object = s):
                    sparqlvalidationquery += f'?{property}shape sh:property [ sh:path <{p}> ; ] .\n'
                    for subj in sorted_graph.subjects(predicate = p, object = s):
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
        # For the time being only unique resolutions of classes are allowed. TODO: Implement multi class resolutions
        if debug > 2: print(f'DEBUG: Validation Query: {query}', file=debugoutput)
        qres = g.query(query)
        if debug > 2: print(f'DEBUG: Result of Validation Query: {list(qres)}', file=debugoutput)
        if len(qres) != 1:
            raise SparqlValidationFailed("Validation of BGP failed. It either contradicts what is defined in SHACL or is too ambigue!")
    else:
        # no ngsi-ld variables found, so do not try to infer the types
        qres = []

    where = ''
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
    """
    
    if debug > 1: print(f'DEBUG: Processing as NGSILD {s, p, o}', file = debugoutput)
    # We got a triple <?var, p, []> where p is a shacle specified property
    # Now we need the ngsild part to determine if it is a relationship or not
    ngsildtype = list(local_ctx['h'].predicates(subject = o))
    ngsildvar =  list(local_ctx['h'].objects(subject = o))
    if len(ngsildtype) != 1 or len(ngsildvar) != 1:
        raise SparqlValidationFailed(f'No matching ngsiltype or ngsildvar found for variable {s.toPython()}')
    if not isinstance(ngsildvar[0], Variable):
        raise SparqlValidationFailed(f'Binding of {s} to concrete iri|literal not (yet) supported. Consider to use a variable and FILTER.')
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
            local_ctx['selvars'][ngsildvar[0].toPython()[1:]] = f'`{attribute_tablename}`.`{ngsildtype[0]}`'
            local_ctx['bounds'][ngsildvar[0].toPython()[1:]] = f'`{attribute_tablename}`.`{ngsildtype[0]}`'
        join_condition = f'{attribute_tablename}.id = {subject_tablename}.`{p}`'
        sql_expression = f'attributes_view AS {attribute_tablename}'
        local_ctx['bgp_tables'][attribute_tablename] = []
        local_ctx['bgp_sql_expression'].append({'statement': f'{sql_expression}', 'join_condition': f'{join_condition}'})
    else:
        # In case of Relationships there are two cases:
        # (1) object_var is not defined
        # (2) object_var is already definied but no subject_var
        if ngsildtype[0] != ngsild['hasObject']:
            raise SparqlValidationFailed("Internal implementation error")
        if not isinstance(ngsildvar[0], Variable):
            raise SparqlValidationFailed(f'Binding {s} to non-variable {ngsildvar[0]} not supported. Consider using a variable and FILTER instead.')
        object_varname = f'{ngsildvar[0].toPython()}'[1:]
        object_sqltable = utils.camelcase_to_snake_case(utils.strip_class(local_ctx['row'][object_varname]))
        object_tablename = f'{object_varname.upper()}TABLE'
        if not object_varname in local_ctx['bounds']:
            # case (1)
            join_condition = f'{attribute_tablename}.id = {subject_tablename}.`{p}`'
            sql_expression = f'attributes_view AS {attribute_tablename}'
            local_ctx['bgp_tables'][attribute_tablename] = []
            local_ctx['bgp_tables'][object_tablename] = []
            local_ctx['bgp_sql_expression'].append({ 'statement': f'{sql_expression}', 'join_condition': f'{join_condition}'})
            local_ctx['bgp_sql_expression'].append({ 'statement': f'{object_sqltable}_view AS {object_tablename}', 'join_condition': f'{object_tablename}.id = {attribute_tablename}.`{ngsildtype[0].toPython()}`'})
            ctx['sql_tables'].append(object_sqltable)
            # if object_varname not in local_ctx['bounds']:
            local_ctx['selvars'][object_varname] = f'{object_tablename}.`id`'
            local_ctx['bounds'][object_varname] = f'{object_tablename}.`id`'
        else:
            # case (2)
            join_condition = f'{attribute_tablename}.`{ngsildtype[0].toPython()}` = {object_tablename}.id'
            sql_expression = f'attributes_view AS {attribute_tablename}'
            local_ctx['bgp_sql_expression'].append( { 'statement': f'{sql_expression}', 'join_condition': f'{join_condition}'})
            join_condition = f'{attribute_tablename}.id = {subject_tablename}.`{p}`'
            sql_expression = f'{subject_sqltable}_view AS {subject_tablename}'
            ctx['sql_tables'].append(subject_sqltable)
            local_ctx['bgp_tables'][attribute_tablename] = []
            local_ctx['bgp_tables'][subject_tablename] = []
            local_ctx['bgp_sql_expression'].append({ 'statement': f'{sql_expression}', 'join_condition': f'{join_condition}'}) 
            if subject_varname not in local_ctx['bounds']:
                local_ctx['selvars'][subject_varname] = f'`{subject_tablename}`.`id`'
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
    """
    # must be  RDF query
    if debug > 1: print(f'Processing as RDF query: {s, p, o}', file = debugoutput) 
    if not isinstance(p, URIRef):
        raise SparqlValidationFailed("NON IRI RDF-predicate not (yet) supported.")
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
    object_is_type = False
    subject_join_condition = None
    if isinstance(s, Variable) and (s in local_ctx['entity_variables'] or isentity(ctx, s)):
        if p == RDF['type']:
            entity = local_ctx['bounds'].get(create_varname(s))    
            if entity is None:
                raise SparqlValidationFailed(f'In triple {s, p, o}: Subject entity not bound but cannot bind object and subject of RDF term at same time. Please consider rearranging terms.')
            entity_table = entity.replace('.id','')
            entity_column = entity.replace('.id','.type')
            column = 'type'
            global_tables = ctx['tables']
            if not entity_table in global_tables:
                global_tables[entity_table] = []    
            global_tables[entity_table].append('type')
            if isinstance(o, Variable):
                #object_is_type = True
                #subject_join_condition = None
                # OK let's process the special case here
                # Two cases: (1) object variable is bound (2) object variable unknown
                
                object_join_bound = get_rdf_join_condition(o, local_ctx['property_variables'], local_ctx['entity_variables'], local_ctx['bounds'])
                if object_join_bound is None:
                    # (2)
                    # bind variable with type column of subject
                    # add variable to local table
                    # if entity_table not in global_tables:
                    #    global_tables[entity_table] = []
                    #global_tables[entity_table].append(column)
                    local_ctx['selvars'][create_varname(o)] = entity_column
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
                local_ctx['where'] = merge_where_expression(local_ctx['where'], f'{entity_column} = \'{o}\'')
                return
        else:
            raise SparqlValidationFailed("Cannot query generic RDF term with NGSI-LD entity subject.")
    else:
        # No special case. Check if subject is non bound and if non bound whether it can be bound
        subject_join_bound = get_rdf_join_condition(s, local_ctx['property_variables'], local_ctx['entity_variables'], local_ctx['bounds'])
        if subject_join_bound is None:
            if not isinstance(s, Variable):
                raise SparqlValidationFailed("Could not resolve {s} and not a variable")
            # Variable not found, needs to be added
            subj_column = f'`{rdftable_name}`.`subject`'
            local_ctx['selvars'][create_varname(s)] = subj_column
            local_ctx['bounds'][create_varname(s)] = subj_column
            subject_join_bound = None    
        subject_join_condition = f'{rdftable_name}.subject = {subject_join_bound}' if subject_join_bound is not None else None
    predicate_join_condition = f'{rdftable_name}.predicate = \'{p.toPython()}\''
    # Process object join condition
    # object variables which are referencing ngsild-entities are forbidden
    if isinstance(o, Variable) and o in local_ctx['entity_variables']:
        raise SparqlValidationFailed(f'Cannot bind NGSI-LD Entities to RDF objects.')
    object_join_bound = get_rdf_join_condition(o, local_ctx['property_variables'], local_ctx['entity_variables'], local_ctx['bounds'])
    if object_join_bound is None:
        if not isinstance(o, Variable):
            raise SparqlValidationFailed("Could not resolve {o} not being a variable")
        # Variable not found, needs to be added
        local_ctx['selvars'][create_varname(o)] = f'{rdftable_name}.object'
        local_ctx['bounds'][create_varname(o)] = f'{rdftable_name}.object'
        object_join_bound = None
    object_join_condition = f'{rdftable_name}.object = {object_join_bound}' if object_join_bound is not None else None
    join_condition = f'{predicate_join_condition}'
    # if we found join condition for subject and object, add them
    if subject_join_condition is not None:
        join_condition = f'{subject_join_condition} and {join_condition}'
    if object_join_condition is not None: join_condition += f' and {object_join_condition}' 
    sql_expression = f'{configs.rdf_table_name} AS {rdftable_name}'
    local_ctx['bgp_tables'][rdftable_name] = []
    local_ctx['bgp_sql_expression'].append( {'statement': f'{sql_expression}', 'join_condition': f'{join_condition}'})
    
                
def translate_BGP(ctx, bgp):
    """Translates a Basic Graph Pattern into SQL term
    
    Assumption is that the model data is provided in NGSI-LD tables and Knowlege data as triples in
    a RDF table

    Args:
        ctx (dictionary): Contains the results and metadata, e.g. variable mapping, resulting sql expression
        bgp (dictionary): BGP structure provided by RDFLib SPARQL parser

    Raises:
        WrongSparqlStructure: Problems with SPARQL metadata, or features which are not implemented
        SparqlValidationFailed: Problems with SPARQL parsing, dependencies
    """
    if debug  > 2: print(f'DEBUG: BGP: {bgp}', file=debugoutput)
    # Assumes a 'Basic Graph Pattern'
    if not bgp.name == 'BGP':
        raise WrongSparqlStructure('No BGP!')
    # Translate set of triples into Graph for later processing
    if len(bgp.triples) == 0:
        bgp['sql_context'] = {}
        return
    h = Graph()
    for s, p, o in bgp.triples:
        h.add((s, p, o))

    property_variables, entity_variables, row = create_ngsild_mappings(ctx, h)

    # before translating, sort the bgp order to allow easier binds
    bgp.triples = sort_triples(ctx['bounds'],bgp.triples, h)

    local_ctx = {}
    local_ctx['bounds'] = ctx["bounds"]
    local_ctx['selvars'] = {}
    local_ctx['where'] = ''
    local_ctx['bgp_sql_expression'] = []
    local_ctx['bgp_tables'] = {}
    local_ctx['property_variables'] = property_variables
    local_ctx['entity_variables'] = entity_variables
    local_ctx['h'] = h
    local_ctx['row'] = row
    
    for s, p, o in bgp.triples:
        # If there are properties or relationships, assume it is a NGSI-LD matter
        if (p.toPython() in properties or p.toPython() in relationships) and isinstance(o, BNode):
            if isinstance(s, Variable):
                process_ngsild_spo(ctx, local_ctx, s, p, o)
        elif p != ngsild['hasValue'] and p != ngsild['hasObject']: 
            # must be  RDF query
            process_rdf_spo(ctx, local_ctx, s, p, o)
           
        else:
            if debug > 1: print(f'DEBUG: Ignoring: {s, p, o}', file = debugoutput)


    bgp_join_conditions = []
    if len(local_ctx['bgp_sql_expression']) != 0:
        map_join_condition(local_ctx['bgp_sql_expression'], local_ctx['bgp_tables'], ctx['tables'])
        #bgp_join_conditions = [bgp_sql_expression[0]['join_condition']]
        bgp_join_conditions = []
        if  local_ctx['where'] != '':
            bgp_join_conditions.append(local_ctx['where'])
    bgp['sql_context'] = create_bgp_context(local_ctx['selvars'], bgp_join_conditions, local_ctx['bgp_sql_expression'], local_ctx['bgp_tables'])
    tables = ctx['tables']
    for table, value in local_ctx['bgp_tables'].items():
        if table not in tables: tables[table] = []
        tables[table] += value
