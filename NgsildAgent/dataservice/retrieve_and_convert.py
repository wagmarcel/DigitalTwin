import sys
import rdflib
import random
from rdflib.namespace import RDF
from rdflib import Variable, URIRef, Literal

ONT = rdflib.Namespace("https://volkswagen.org/vass/v0.9/ontology#")
USECASE = rdflib.Namespace("https://volkswagen.org/vass/v0.9/usecase#")

prefixes = f"""
PREFIX ontology: <{ONT}>
PREFIX usecase: <{USECASE}>
PREFIX rdf: <{RDF}>
"""

def ruc(graph, class_uri, attr_uri, params_query, values_query):
    query = prefixes + params_query
    qres = graph.query(query)
    #print(f"now querying {query}")
    param_array = []   
    for row in qres:
        #print(f'found parameters {row.hasVarName.toPython()}')
        param_dict = {}
        param_dict['DataType'] = row.hasDataType.toPython()
        param_dict['Value']= None
        param_dict['VarName'] = row.hasVarName.toPython()
        param_array.append(param_dict)
    fetch(param_array)
    evaluate(graph, param_array,values_query)

# This function will receive an array of dictionaries containing the needed parameters
# to read out data from machines or databases.
# The empty "value" field needs to be filled out.
def fetch(param_array):
    for param_dict in param_array:
        data_type = param_dict['DataType']
        var_name = param_dict['VarName']
        if data_type == 'http://www.w3.org/2001/XMLSchema#boolean':
            param_dict['Value'] = Literal(random.choice([True, False]))
            print(f"I fetched {param_dict['Value']} for varname {var_name} with data type {data_type}")


def evaluate(graph, param_array, values_query):
    bindings = {}
    for param_dict in param_array:
        value = param_dict['Value']
        var_name = param_dict['VarName']
        if value is not None:
            bindings[Variable(var_name)] = value
    query = prefixes + values_query
    qres = graph.query(query, initBindings=bindings)
    for row in qres:
        print(f"Evaluation result {row}")