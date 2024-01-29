import sys
import rdflib
import random
import socket
import requests
import json
from rdflib.namespace import RDF
from rdflib import Variable, URIRef, Literal

ONT = rdflib.Namespace("https://volkswagen.org/vass/v0.9/ontology#")
USECASE = rdflib.Namespace("https://volkswagen.org/vass/v0.9/usecase#")
tokenfile = "token.json"
devicefile = "../data/device.json"
host = '127.0.0.1'
port = 7070

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
    value = evaluate(graph, param_array,values_query)
    send(value, attr_uri)



##########################################################################################
# This function will receive an array of dictionaries containing the needed parameters
# to read out data from machines or databases.
# The empty "value" field needs to be filled out.
##########################################################################################
def fetch(param_array):
    for param_dict in param_array:
        data_type = param_dict['DataType']
        var_name = param_dict['VarName']
        if data_type == 'http://www.w3.org/2001/XMLSchema#boolean':
            param_dict['Value'] = Literal(random.choice([True, False]))
            print(f"I fetched {param_dict['Value']} for varname {var_name} with data type {data_type}")

############################################################################################
############################################################################################

def evaluate(graph, param_array, values_query):
    bindings = {}
    for param_dict in param_array:
        value = param_dict['Value']
        var_name = param_dict['VarName']
        if value is not None:
            bindings[Variable(var_name)] = value
    query = prefixes + values_query
    #print(f"now querying {query}")
    qres = graph.query(query, initBindings=bindings)
    result = None
    for row in qres:
        print(f"Evaluation result {row}")
        result = row.value
    return result


def send(value, attribute):
    if isinstance(value, Literal):
        # Send over mqtt/device-agent
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        payload = f'{{ "n": "{attribute}", "v": "{value.toPython()}"}}'
        print(f"sent {payload}")
        client_socket.sendall(payload.encode('ascii'))
        client_socket.close()
    elif isinstance(value, URIRef):
        # send over REST
        update_attr(value, attribute)
        
    else:
        print("Warning: Could not determine how to send data")
    
    
def update_attr(value, attribute):
    with open(tokenfile, 'r') as file:
        token = file.read()
        #print(token)

    entity_id = "your-entity-id"
    with open(devicefile, 'r') as file:
        devicedata = json.load(file)

    if "device_id" in devicedata:
        entity_id = devicedata['device_id']
        #print(f"found device_id {entity_id}")
    base_uri = "http://ngsild.local"

    authorization = f'Bearer {token}'
    headers = {
        'Content-Type': 'application/ld+json',
        'Authorization': authorization.rstrip()
    }

    # Define the attribute update payload
    # Replace 'attributeName' with your actual attribute name and set its value
    attribute_update = {
        "@context": [
            "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context-v1.3.jsonld"
        ],
        f"{attribute.toPython()}": {
            "type": "Property",
            "value": {"@id": f"{value.toPython()}"}
        }
    }
    #print(f"{attribute_update}")
    #return
    # Make the PATCH request to update the attribute
    response = requests.patch(f"{base_uri}/ngsi-ld/v1/entities/{entity_id}/attrs",
                            headers=headers,
                            data=json.dumps(attribute_update))

    # Check the response
    if response.status_code == 204:
        print("Attribute updated successfully.")
    else:
        print(f"Failed to update attribute: {response.status_code} {response.text}")