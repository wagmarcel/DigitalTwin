import sys
import rdflib
import owlrl
from rdflib.namespace import RDF
from rdflib import Variable

ONT = rdflib.Namespace("https://volkswagen.org/vass/v0.9/ontology#")
USECASE = rdflib.Namespace("https://volkswagen.org/vass/v0.9/usecase#")
get_maps_query = f"""
PREFIX ont: <{ONT}>
PREFIX usecase: <{USECASE}>
PREFIX rdf: <{RDF}>
SELECT ?paramsQuery ?valuesQuery 
WHERE{{ 
    ?map rdf:type ont:Mapping .
    ?map ont:mapAttribute ?targetAttr .
    ?map ont:mapClass ?targetClass .
    ?map ont:getParams ?paramsQuery .
    ?map ont:getValues ?valuesQuery .
}}
"""
usage = """
normalization <shacl.ttl> <usecase.ttl> <ontology.ttl> <root.ttl> 
"""
if len(sys.argv) < 5:
    print(usage)
    exit(1)

shaclfile = sys.argv[1]
usecasefile = sys.argv[2]
ontologyfile = sys.argv[3]
rootfile = sys.argv[4]

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

#e = rdflib.Graph()
#rdfs = owlrl.RDFSClosure.RDFS_Semantics(g, axioms=True, daxioms=True, rdfs=True).closure()
#rdfs = owlrl.OWLRLExtras.OWLRL_Extension(g, axioms=True, daxioms=True, rdfs=True).closure()
#owlrl.DeductiveClosure(owlrl.RDFS_Semantics, improved_datatypes = False).expand(g)

bindings = {Variable("targetClass"): USECASE.Process, Variable("targetAttr"): USECASE.hasState}
qres = g.query(get_maps_query, initBindings=bindings)
for row in qres:
    print(f'Found mappings: {row.paramsQuery} and  {row.valuesQuery}')
