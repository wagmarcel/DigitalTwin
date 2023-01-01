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
from rdflib import Namespace, term

hasObjectURI = term.URIRef("https://uri.etsi.org/ngsi-ld/hasObject")
stateURI = term.URIRef("https://industry-fusion.com/types/v0.9/state")
hasFilterURI = term.URIRef("https://industry-fusion.com/types/v0.9/hasFilter")
hasValueURI = term.URIRef("https://uri.etsi.org/ngsi-ld/hasValue")
target_class = term.URIRef("https://industry-fusion.com/v0.9/cutter")


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
    mock_ctx = MagicMock()
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