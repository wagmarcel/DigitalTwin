import sys
import rdflib
from rdflib.namespace import RDF
from rdflib import Variable, URIRef
import retrieve_and_convert

ONT = rdflib.Namespace("https://volkswagen.org/vass/v0.9/ontology#")
USECASE = rdflib.Namespace("https://volkswagen.org/vass/v0.9/usecase#")
get_maps_query = f"""
PREFIX ontology: <{ONT}>
PREFIX usecase: <{USECASE}>
PREFIX rdf: <{RDF}>
SELECT ?paramsQuery ?valuesQuery 
WHERE{{ 
    ?map rdf:type ontology:Mapping .
    ?map ontology:mapAttribute ?targetAttr .
    ?map ontology:mapClass ?targetClass .
    ?map ontology:getParams ?paramsQuery .
    ?map ontology:getValues ?valuesQuery .
}}
"""
usage = """
dataservice <kmsdir> <class iri> <attribute iri> 
"""
if len(sys.argv) < 4:
    print(usage)
    exit(1)

kmsdir=sys.argv[1]
target_class = sys.argv[2]
target_attr = sys.argv[3]

shaclfile = f'{kmsdir}/shacl.ttl'
usecasefile = f'{kmsdir}/usecase.ttl'
ontologyfile = f'{kmsdir}/ontology.ttl'
rootfile = f'{kmsdir}/root.ttl'

print(f'Files to read: {shaclfile}, {usecasefile}, {ontologyfile}, {rootfile}')
print(f'Class: {target_class}')
print(f'Attribute: {target_attr}')

g = rdflib.Graph()
g.parse(shaclfile)
h = rdflib.Graph()
h.parse(usecasefile)
i = rdflib.Graph()
i.parse(ontologyfile)
j = rdflib.Graph()
j.parse(rootfile)

g += h
g += i
g += j


target_class = URIRef(target_class) #USECASE.Process
target_attr = URIRef(target_attr) #USECASE.hasNumericalState

bindings = {Variable("targetClass"): target_class, Variable("targetAttr"): target_attr}
#print(f'{bindings}')
qres = g.query(get_maps_query, initBindings=bindings)
for row in qres:
    #print(f'Found mappings: {row.paramsQuery} and  {row.valuesQuery}')
    retrieve_and_convert.ruc(g, target_class, target_attr, row.paramsQuery, row.valuesQuery)
if len(qres) == 0:
    print("Warning: No attribute sent.")