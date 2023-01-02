#
# Copyright (c) 2022 Intel Corporation
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

from unittest.mock import MagicMock, patch
import lib.sparql_to_sql
from bunch import Bunch
from rdflib import Namespace, term, RDF

hasObjectURI = term.URIRef("https://uri.etsi.org/ngsi-ld/hasObject")
stateURI = term.URIRef("https://industry-fusion.com/types/v0.9/state")
hasFilterURI = term.URIRef("https://industry-fusion.com/types/v0.9/hasFilter")
hasValueURI = term.URIRef("https://uri.etsi.org/ngsi-ld/hasValue")
target_class = term.URIRef("https://industry-fusion.com/v0.9/cutter")
cutter = term.URIRef("cutter")

def test_create_ngsild_mappings(monkeypatch):
    class Graph:
        def query(self, sparql):
            assert "?this rdfs:subClassOf <https://industry-fusion.com/v0.9/cutter> ." in sparql
            assert "?thisshape sh:targetClass ?this .\n?thisshape sh:property [ sh:path \
<https://industry-fusion.com/types/v0.9/hasFilter> ; sh:property [ sh:path \
ngsild:hasObject;  sh:class ?f ] ] ." in sparql
            assert "?v2shape sh:targetClass ?v2 .\n?v2shape sh:property [ sh:path \
<https://industry-fusion.com/types/v0.9/state> ; ] ." in sparql
            assert "?v1shape sh:targetClass ?v1 .\n?v1shape sh:property [ sh:path \
<https://industry-fusion.com/types/v0.9/state> ; ] ." in sparql
            assert "filter(?fshape = ?v2shape && ?thisshape = ?v1shape)" in sparql
            return ['row']
    relationships = {
        "https://industry-fusion.com/types/v0.9/hasFilter": True     
    }
    properties = {
        "https://industry-fusion.com/types/v0.9/state": True
    }
    g = Graph()
    monkeypatch.setattr(lib.sparql_to_sql, "properties", properties)
    monkeypatch.setattr(lib.sparql_to_sql, "g", g)
    monkeypatch.setattr(lib.sparql_to_sql, "relationships", relationships)
    mock_graph = MagicMock()
    ctx = {'namespace_manager': None, 
            'PV': None,
            'pass': 0,
            'target_used': False,
            'table_id': 0,
            'classes': {'this': target_class},
            'sql_tables': ['cutter', 'attributes'],
            'bounds': {'this': 'THISTABLE.id'},
            'tables': {'THISTABLE': ['id']},
            'target_sql': '',
            'target_where': '',
            'target_modifiers': [],
            'target_ctx': {
                'bounds': {'this': 'THISTABLE.id'}, 
                'join_conditions': [],
                'sql_expression': [{'statement': f'cutter_view as THISTABLE',
                                                'join_condition': ''}], 
                'tables': ['THISTABLE']
            }
    }
    
    mock_graph.__iter__.return_value =  [(term.BNode('1'), hasObjectURI, term.Variable('f')),
                                     (term.Variable('f'), stateURI, term.BNode('2')),
                                     (term.Variable('this'), hasFilterURI, term.BNode('1')),
                                     (term.Variable('this'), stateURI, term.BNode('3')),
                                     (term.BNode('2'), hasValueURI, term.Variable('v2')),
                                     (term.BNode('3'), hasValueURI, term.Variable('v1'))]
    mock_graph.triples = MagicMock(side_effect=[
        [(term.Variable('f'), stateURI, term.BNode('2'))],
         [(term.Variable('this'), hasFilterURI, term.BNode('1')),
          (term.Variable('this'), stateURI, term.BNode('3'))],
         [(term.BNode('2'), hasValueURI, term.Variable('v2'))],
         [(term.BNode('3'), hasValueURI, term.Variable('v1'))]
    ])
    mock_graph.value = MagicMock(side_effect=[
        None, term.Variable('f'), None
    ])
    mock_graph.predicates = MagicMock(side_effect=[
        [stateURI], [stateURI]
    ])
    mock_graph.subjects = MagicMock(side_effect=[
        [term.Variable('f')], [term.Variable('this')]
    ])
    property_variables, entity_variables, row = lib.sparql_to_sql.create_ngsild_mappings(ctx, mock_graph)
    assert property_variables == {
        term.Variable('v2'): True,
        term.Variable('v1'): True
    }
    assert entity_variables == {
        term.Variable('f'): True,
        term.Variable('this'): True
    }
    assert row == 'row'


@patch('lib.sparql_to_sql.get_random_string')
@patch('lib.sparql_to_sql.create_varname')
@patch('lib.sparql_to_sql.create_tablename')
@patch('lib.sparql_to_sql.isentity')
def test_process_rdf_spo_predicate_is_rdftype_object_is_iri(mock_isentity, mock_create_table_name, mock_create_varname, mock_get_random_string, monkeypatch):
    relationships = {
        "https://industry-fusion.com/types/v0.9/hasFilter": True
    }
    properties = {
        "https://industry-fusion.com/types/v0.9/state": True
    }
    monkeypatch.setattr(lib.sparql_to_sql, "properties", properties)
    monkeypatch.setattr(lib.sparql_to_sql, "relationships", relationships)
    mock_create_table_name.return_value = 'testtable'
    mock_isentity.return_value = True
    mock_create_varname.return_value = 'f'
    mock_get_random_string.return_value = ''
    ctx = {
        'namespace_manager': None,
        'bounds': {'this': 'THISTABLE.id'},
        'tables': {'THISTABLE': ['id']}
    }
    local_ctx = {
        'bounds': {'this': 'THISTABLE.id', 'f': 'FILTER.id'},
        'selvars': {},
        'where': '',
        'bgp_sql_expression': [],
        'bgp_tables': {},
        'property_variables': {},
        'entity_variables': {},
        'h': {},
        'row': 'row'
    }
    s = term.Variable('f')
    p = RDF['type']
    o = term.URIRef('https://example.com/obj')
    lib.sparql_to_sql.process_rdf_spo(ctx, local_ctx, s, p, o)
    assert local_ctx['where'] == "FILTER.type = 'https://example.com/obj'"
    assert local_ctx['bounds'] == {'this': 'THISTABLE.id', 'f': 'FILTER.id'}


@patch('lib.sparql_to_sql.get_rdf_join_condition')
@patch('lib.sparql_to_sql.get_random_string')
@patch('lib.sparql_to_sql.create_tablename')
@patch('lib.sparql_to_sql.isentity')
def test_process_rdf_spo_predicate_is_rdf_type_object_is_variable(mock_isentity, mock_create_table_name, mock_get_random_string, mock_get_rdf_join_condiion, monkeypatch):
    def create_varname(var):
        if var == term.Variable('f'): return 'f'
        if var == term.Variable('x'): return 'x'

    relationships = {
        "https://industry-fusion.com/types/v0.9/hasFilter": True
    }
    properties = {
        "https://industry-fusion.com/types/v0.9/state": True
    }
    monkeypatch.setattr(lib.sparql_to_sql, "properties", properties)
    monkeypatch.setattr(lib.sparql_to_sql, "relationships", relationships)
    monkeypatch.setattr(lib.sparql_to_sql, "create_varname", create_varname)
    mock_create_table_name.return_value = 'testtable'
    mock_isentity.return_value = True
    mock_get_random_string.return_value = ''
    mock_get_rdf_join_condiion.return_value = 'condition'
    ctx = {
        'namespace_manager': None,
        'bounds': {'this': 'THISTABLE.id'},
        'tables': {'THISTABLE': ['id']}
    }
    local_ctx = {
        'bounds': {'this': 'THISTABLE.id', 'f': 'FILTER.id', 'x': 'xtable.subject'},
        'selvars': {},
        'where': '',
        'bgp_sql_expression': [],
        'bgp_tables': {},
        'property_variables': {},
        'entity_variables': {},
        'h': {},
        'row': 'row'
    }
    s = term.Variable('f')
    p = RDF['type']
    o = term.Variable('x')
    lib.sparql_to_sql.process_rdf_spo(ctx, local_ctx, s, p, o)
    assert local_ctx['where'] == 'FILTER.type = xtable.subject'
    assert local_ctx['bounds'] == {'this': 'THISTABLE.id', 'f': 'FILTER.id', 'x': 'xtable.subject'}
    ctx = {
        'namespace_manager': None,
        'bounds': {'this': 'THISTABLE.id'},
        'tables': {'THISTABLE': ['id']}
    }
    local_ctx = {
        'bounds': {'this': 'THISTABLE.id', 'f': 'FILTER.id', 'x': 'xtable.subject'},
        'selvars': {},
        'where': '',
        'bgp_sql_expression': [],
        'bgp_tables': {},
        'property_variables': {},
        'entity_variables': {},
        'h': {},
        'row': 'row'
    }
    mock_get_rdf_join_condiion.return_value = None

    s = term.Variable('f')
    p = RDF['type']
    o = term.Variable('x')
    lib.sparql_to_sql.process_rdf_spo(ctx, local_ctx, s, p, o)
    assert local_ctx['selvars'] == {'x': 'FILTER.type'}
    assert local_ctx['bounds'] == {'this': 'THISTABLE.id', 'f': 'FILTER.id', 'x': 'FILTER.type'}


@patch('lib.sparql_to_sql.get_rdf_join_condition')
@patch('lib.sparql_to_sql.get_random_string')
@patch('lib.sparql_to_sql.create_varname')
@patch('lib.sparql_to_sql.create_tablename')
@patch('lib.sparql_to_sql.isentity')
def test_process_rdf_spo_subject_is_no_entity(mock_isentity, mock_create_table_name, mock_create_varname, mock_get_random_string, mock_get_rdf_join_condition, monkeypatch):
    relationships = {
        "https://industry-fusion.com/types/v0.9/hasFilter": True
    }
    properties = {
        "https://industry-fusion.com/types/v0.9/state": True
    }
    monkeypatch.setattr(lib.sparql_to_sql, "properties", properties)
    monkeypatch.setattr(lib.sparql_to_sql, "relationships", relationships)
    mock_create_table_name.return_value = 'testtable'
    mock_isentity.return_value = False
    mock_create_varname.return_value = 'f'
    mock_get_random_string.return_value = ''
    mock_get_rdf_join_condition.return_value = 'condition'
    ctx = {
        'namespace_manager': None,
        'bounds': {'this': 'THISTABLE.id'},
        'tables': {'THISTABLE': ['id']}
    }
    local_ctx = {
        'bounds': {'this': 'THISTABLE.id', 'f': 'FILTER.id'},
        'selvars': {},
        'where': '',
        'bgp_sql_expression': [],
        'bgp_tables': {},
        'property_variables': {},
        'entity_variables': {},
        'h': {},
        'row': 'row'
    }
    s = term.Variable('f')
    p = RDF['type']
    o = term.URIRef('https://example.com/obj')
    lib.sparql_to_sql.process_rdf_spo(ctx, local_ctx, s, p, o)
    assert local_ctx['bgp_sql_expression'] == [{'statement': 'rdf AS testtable', 
                                                'join_condition': "testtable.subject = condition and testtable.predicate = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type' and testtable.object = condition"}]
    assert local_ctx['bounds'] == {'this': 'THISTABLE.id', 'f': 'FILTER.id'}
    assert local_ctx['bgp_tables'] == {'testtable': []}
    
    mock_get_rdf_join_condition.return_value = None
    ctx = {
        'namespace_manager': None,
        'bounds': {'this': 'THISTABLE.id'},
        'tables': {'THISTABLE': ['id']}
    }
    local_ctx = {
        'bounds': {'this': 'THISTABLE.id', 'f': 'FILTER.id'},
        'selvars': {},
        'where': '',
        'bgp_sql_expression': [],
        'bgp_tables': {},
        'property_variables': {},
        'entity_variables': {},
        'h': {},
        'row': 'row'
    }
    p = term.URIRef('test')
    o = term.Variable('x')
    lib.sparql_to_sql.process_rdf_spo(ctx, local_ctx, s, p, o)
    assert local_ctx['bgp_sql_expression'] == [{'statement': 'rdf AS testtable', 
                                                'join_condition': "testtable.predicate = 'test'"}]
    assert local_ctx['bounds'] == {'this': 'THISTABLE.id', 'f': 'testtable.object'}
    assert local_ctx['bgp_tables'] == {'testtable': []}
    assert local_ctx['selvars'] == {'f': 'testtable.object'}


@patch('lib.sparql_to_sql.get_random_string')
@patch('lib.sparql_to_sql.create_varname')
@patch('lib.sparql_to_sql.create_tablename')
@patch('lib.sparql_to_sql.isentity')
def test_process_ngsild_spo_hasValue(mock_isentity, mock_create_table_name, mock_create_varname, mock_get_random_string, monkeypatch):
    relationships = {
        "https://industry-fusion.com/types/v0.9/hasFilter": True
    }
    properties = {
        "https://industry-fusion.com/types/v0.9/state": True
    }
    monkeypatch.setattr(lib.sparql_to_sql, "properties", properties)
    monkeypatch.setattr(lib.sparql_to_sql, "relationships", relationships)
    mock_create_table_name.return_value = 'testtable'
    mock_isentity.return_value = True
    mock_create_varname.return_value = 'f'
    mock_get_random_string.return_value = ''
    mock_h = MagicMock()
    mock_h.predicates.return_value = [hasValueURI]
    mock_h.objects.return_value = [term.Variable('v1')]
    ctx = {
        'namespace_manager': None,
        'bounds': {'this': 'THISTABLE.id'},
        'tables': {'THISTABLE': ['id']}
    }
    # test with unbound v1
    local_ctx = {
        'bounds': {'this': 'THISTABLE.id'},
        'selvars': {},
        'where': '',
        'bgp_sql_expression': [],
        'bgp_tables': {},
        'property_variables': {},
        'entity_variables': {},
        'h': mock_h,
        'row': {'f': 'ftable'}
    }
    s = term.Variable('f')
    p = stateURI
    o = term.URIRef('https://example.com/obj')
    lib.sparql_to_sql.process_ngsild_spo(ctx, local_ctx, s, p, o)
    assert local_ctx['bgp_tables'] == {'FSTATETABLE': []}
    assert local_ctx['bounds'] == {'this': 'THISTABLE.id', 'v1': '`FSTATETABLE`.`https://uri.etsi.org/ngsi-ld/hasValue`'}
    assert local_ctx['selvars'] == {'v1': '`FSTATETABLE`.`https://uri.etsi.org/ngsi-ld/hasValue`'}
    assert local_ctx['bgp_sql_expression'] == [{'statement': 'attributes_view AS FSTATETABLE', 'join_condition': 'FSTATETABLE.id = FTABLE.`https://industry-fusion.com/types/v0.9/state`'}]
    
    # Test with bound v1
    mock_create_varname.return_value = 'v1'

    ctx = {
        'namespace_manager': None,
        'bounds': {'this': 'THISTABLE.id'},
        'tables': {'THISTABLE': ['id']}
    }
    local_ctx = {
        'bounds': {'this': 'THISTABLE.id', 'f': 'FILTER.id', 'v1': 'V1TABLE.id'},
        'selvars': {},
        'where': '',
        'bgp_sql_expression': [],
        'bgp_tables': {},
        'property_variables': {},
        'entity_variables': {},
        'h': mock_h,
        'row': {'f': 'ftable'}
    }
    s = term.Variable('f')
    p = stateURI
    o = term.URIRef('https://example.com/obj')
    
    lib.sparql_to_sql.process_ngsild_spo(ctx, local_ctx, s, p, o)
    assert local_ctx['bgp_tables'] == {'FSTATETABLE': []}
    assert local_ctx['bounds'] == {'this': 'THISTABLE.id', 'f': 'FILTER.id', 'v1': 'V1TABLE.id'}
    assert local_ctx['selvars'] == {}
    assert local_ctx['bgp_sql_expression'] == [{'statement': 'attributes_view AS FSTATETABLE', 'join_condition': 'FSTATETABLE.id = FTABLE.`https://industry-fusion.com/types/v0.9/state`'}]


@patch('lib.sparql_to_sql.get_random_string')
@patch('lib.sparql_to_sql.create_varname')
@patch('lib.sparql_to_sql.create_tablename')
@patch('lib.sparql_to_sql.isentity')
def test_process_ngsild_spo_hasObject(mock_isentity, mock_create_table_name, mock_create_varname, mock_get_random_string, monkeypatch):
    relationships = {
        "https://industry-fusion.com/types/v0.9/hasFilter": True
    }
    properties = {
        "https://industry-fusion.com/types/v0.9/state": True
    }
    monkeypatch.setattr(lib.sparql_to_sql, "properties", properties)
    monkeypatch.setattr(lib.sparql_to_sql, "relationships", relationships)
    mock_create_table_name.return_value = 'testtable'
    mock_isentity.return_value = True
    mock_create_varname.return_value = 'f'
    mock_get_random_string.return_value = ''
    mock_h = MagicMock()
    mock_h.predicates.return_value = [hasObjectURI]
    mock_h.objects.return_value = [term.Variable('f')]
    ctx = {
        'namespace_manager': None,
        'bounds': {'this': 'THISTABLE.id'},
        'tables': {'THISTABLE': ['id']},
         'sql_tables': []
    }
    # test with unbound v1
    local_ctx = {
        'bounds': {'this': 'THISTABLE.id'},
        'selvars': {},
        'where': '',
        'bgp_sql_expression': [],
        'bgp_tables': {},
        'property_variables': {},
        'entity_variables': {},
        'h': mock_h,
        'row': {'f': 'ftable'}
    }
    s = term.Variable('f')
    p = hasFilterURI
    o = term.BNode('1')
    lib.sparql_to_sql.process_ngsild_spo(ctx, local_ctx, s, p, o)
    assert local_ctx['bgp_tables'] == {'FHAS_FILTERTABLE': [], 'FTABLE': []}
    assert local_ctx['bounds'] == {'this': 'THISTABLE.id', 'f': 'FTABLE.`id`'}
    assert local_ctx['selvars'] == {'f': 'FTABLE.`id`'}
    assert local_ctx['bgp_sql_expression'] == [
        {'statement': 'attributes_view AS FHAS_FILTERTABLE', 'join_condition': 'FHAS_FILTERTABLE.id = FTABLE.`https://industry-fusion.com/types/v0.9/hasFilter`'},
        {'statement': 'ftable_view AS FTABLE', 'join_condition': 'FTABLE.id = FHAS_FILTERTABLE.`https://uri.etsi.org/ngsi-ld/hasObject`'}]
    
    # Test with bound v1
    mock_create_varname.return_value = 'v1'

    ctx = {
        'namespace_manager': None,
        'bounds': {'this': 'THISTABLE.id'},
        'tables': {'THISTABLE': ['id']},
         'sql_tables': []
    }
    local_ctx = {
        'bounds': {'this': 'THISTABLE.id', 'c': 'CUTTER.id'},
        'selvars': {},
        'where': '',
        'bgp_sql_expression': [],
        'bgp_tables': {},
        'property_variables': {},
        'entity_variables': {},
        'h': mock_h,
        'row': {'c': 'ctable', 'f': 'ftable'}
    }
    s = term.Variable('c')
    p = hasFilterURI
    o = term.URIRef('https://example.com/obj')
    
    lib.sparql_to_sql.process_ngsild_spo(ctx, local_ctx, s, p, o)
    assert local_ctx['bgp_tables'] == {'CHAS_FILTERTABLE': [], 'FTABLE': []}
    assert local_ctx['bounds'] == {'this': 'THISTABLE.id', 'c': 'CUTTER.id', 'f': 'FTABLE.`id`'}
    assert local_ctx['selvars'] == {'f': 'FTABLE.`id`'}
    assert local_ctx['bgp_sql_expression'] == [
        {'statement': 'attributes_view AS CHAS_FILTERTABLE', 'join_condition': 'CHAS_FILTERTABLE.id = CTABLE.`https://industry-fusion.com/types/v0.9/hasFilter`'},
        {'statement': 'ftable_view AS FTABLE', 'join_condition': 'FTABLE.id = CHAS_FILTERTABLE.`https://uri.etsi.org/ngsi-ld/hasObject`'}]


@patch('lib.sparql_to_sql.copy')
def test_sort_triples(mock_copy, monkeypatch):
    def create_varname(var):
        if var == term.Variable('f'): return 'f'
        if var == term.Variable('this'): return 'this'
    relationships = {
        "https://industry-fusion.com/types/v0.9/hasFilter": True
    }
    properties = {
        "https://industry-fusion.com/types/v0.9/state": True
    }
    monkeypatch.setattr(lib.sparql_to_sql, "properties", properties)
    monkeypatch.setattr(lib.sparql_to_sql, "relationships", relationships)
    monkeypatch.setattr(lib.sparql_to_sql, "create_varname", create_varname)
    bounds = {'this': 'THISTABLE.id'}
    triples = [
        (term.Variable('f'), stateURI, term.BNode('2')),
        (term.BNode('1'), hasObjectURI, term.Variable('f')),
        (term.Variable('this'), hasFilterURI, term.BNode('1')),
        ((term.BNode('2'), hasValueURI, term.Variable('v2')))
        ]
    mock_copy.deepcopy.return_value = bounds
    graph = MagicMock()
    graph.triples = MagicMock(side_effect=[
        [(term.BNode('2'), hasValueURI, term.Variable('v2'))],
        [(term.BNode('2'), hasValueURI, term.Variable('v2'))],
        [(term.BNode('1'), hasObjectURI, term.Variable('f'))],
        [(term.BNode('2'), hasValueURI, term.Variable('v2'))]
        ])
    result = lib.sparql_to_sql.sort_triples(bounds, triples, graph)
    assert result[0] == (term.BNode('1'), hasObjectURI, term.Variable('f'))
    assert result[1] == (term.Variable('this'), hasFilterURI, term.BNode('1'))
    assert result[2] == (term.Variable('f'), stateURI, term.BNode('2'))
    assert result[3] == ((term.BNode('2'), hasValueURI, term.Variable('v2')))