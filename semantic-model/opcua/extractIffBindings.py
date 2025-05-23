#!/usr/bin/env python3
#
# Copyright (c) 2025 Intel Corporation
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
import urllib
import random
import string
from lib.utils import warnings, print_warning
from collections import defaultdict
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import OWL, RDF, RDFS, XSD
import argparse
import lib.utils as utils
from lib.utils import RdfUtils, OntologyLoader, NULL_IRI, NGSILD
from lib.bindings import Bindings
from lib.jsonld import JsonLd
from lib.entity import Entity
from lib.shacl import Shacl

warnings.filterwarnings("ignore", message=".*anyType is not defined in namespace XSD.*")
attribute_prefix = 'has'



def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='\
parse nodeset instance and create ngsi-ld model')

    parser.add_argument('mapping', help='Path to the mapping ttl file which contains the IFFMappingsFolder Object.')
    parser.add_argument('-fi', '--folder-id',
                        help='Id of IFFMappingFolder Object',
                        required=False,
                        default=42)
    parser.add_argument('-bv', '--binding-version',
                        help='Verion of the binding model.',
                        required=False,
                        default="0.1")
    parser.add_argument('-bn', '--binding-namespace',
                        help='Namespace prefix for binding ontology.',
                        required=False,
                        default="https://industry-fusion.org/UA/Bindings/")
    parser.add_argument('-b', '--bindings',
                        help='Filename of bindings output file',
                        required=False,
                        default='bindings_iffmodel.ttl')
    parser.add_argument('-i', '--instance-file',
                        help='Filename of instances file contating entity Ids',
                        required=False,
                        default='instances.jsonld')
    parser.add_argument('-n', '--iffmapping-namespace',
                        default='https://industry-fusion.org/UA/Mapping/',
                        help='Overwrite Namespace for IFF mapping ontology.)',
                        required=False)
    parsed_args = parser.parse_args(args)
    return parsed_args


def get_bindings(graph, iffmappingns, basens, opcuans, iffmappingfolder_id):
    """
    Get a list of all attribute bindings from the IFF Mappings ontology.

    This function queries an RDF graph to retrieve attribute bindings associated 
    with a specific folder ID in the IFF Mappings ontology. The query extracts 
    details such as the attribute name, type, logic expression, and entity selector.

        graph (rdflib.Graph): The RDF graph to query.
        iffmappingns (rdflib.Namespace): The namespace for the IFF Mapping ontology.
        basens (rdflib.Namespace): The base namespace for the RDF graph.
        opcuans (rdflib.Namespace): The OPC UA namespace for the RDF graph.
        iffmappingfolder_id (str): The folder ID to filter the query.

    Returns:
        list: A list of query results, where each result contains the following:
            - attributebinding (rdflib.term.URIRef): The URI of the attribute binding.
            - name (rdflib.term.URIRef): The URI of the attribute name.
            - type (rdflib.term.URIRef or None): The URI of the attribute type, if available.
            - logicExpression (rdflib.term.Literal or None): The logic expression, if available.
            - entitySelector (rdflib.term.Literal or None): The entity selector, if available.
    """
    query = """
  SELECT
  ?attributebinding ?name ?type ?logicExpression ?entitySelector
  where {{
    BIND("{folderid}" as ?folderid)
    ?folder base:hasNodeId ?nodeid .
    ?folder base:hasNamespace ?namespace .
    ?namespace base:hasUri ?iffmappingns .
    FILTER(?nodeid = ?folderid && ?iffmappingns = STR(iffmappingns:))
    ?folder opcua:Organizes ?attributebinding .
    OPTIONAL{{
      ?attributebinding opcua:HasComponent ?namenode .
      ?namenode base:hasBrowseName "AttributeName" .
      ?namenode base:hasValue ?namestr .
    }}
     OPTIONAL{{
      ?attributebinding opcua:HasComponent ?typenode .
      ?typenode base:hasBrowseName "NGSILDAttributeType" .
      ?typenode base:hasValue ?typeenum .
      ?type a iffmappingns:NGSILDAttribute .
      ?type base:hasValueNode ?typevaluenode .
      ?typevaluenode base:hasEnumValue ?typeenum .
    }}
    OPTIONAL{{
      ?attributebinding opcua:HasComponent ?lenode .
      ?lenode base:hasBrowseName "LogicExpression" .
      ?lenode base:hasValue ?logicExpression .
    }}
    OPTIONAL{{
      ?attributebinding opcua:HasComponent ?esnode .
      ?esnode base:hasBrowseName "EntitySelector" .
      ?esnode base:hasValue ?entitySelector .
    }}
	BIND(IRI(?namestr) as ?name)
}}
    """.format(folderid=iffmappingfolder_id)
    initNs = {"iffmappingns": iffmappingns, "base": basens, "opcua": opcuans}
    result = graph.query(query, initNs=initNs)
    return list(result)

def get_attribute_parameter(graph, iffmappingns, basens, opcuans, iffmappingfolder_id):
    """
        Retrieve a list of attribute bindings from the IFF mappings ontology.

        This function queries an RDF graph to extract attribute bindings and their associated parameters 
        from the IFF mappings ontology. It returns a dictionary where the keys are attribute bindings 
        and the values are lists of associated parameters.

            graph (rdflib.Graph): The RDF graph to query.
            iffmappingns (rdflib.Namespace): The namespace of the IFF Mapping Ontology.
            basens (rdflib.Namespace): The base namespace for the graph.
            opcuans (rdflib.Namespace): The OPC UA namespace for the graph.
            iffmappingfolder_id (str): The folder ID to filter the query.

        Returns:
            list: A list of dictionaries where each key is an attribute binding and the value is a list 
                of associated parameters. Each parameter includes optional logic variables and variable 
                details such as identifier type, namespace, and node ID.

        Notes:
            - The query uses SPARQL to extract data from the RDF graph.
            - The function binds the folder ID and namespace to filter the results.
            - Optional parameters such as logic variables and variable details are included if available.
    """
    query = """
  SELECT
  ?attributebinding ?logicVariable ?varidtype ?varid ?varns ?datatype
  where {{
    BIND( "{folderid}" as ?folderid)
    ?folder base:hasNodeId ?nodeid .
    ?folder base:hasNamespace ?namespace .
    ?namespace base:hasUri ?iffmappingns .
    FILTER(?nodeid = ?folderid && ?iffmappingns = STR(iffmappingns:))
    ?folder opcua:Organizes ?attributebinding .
  	?attributebinding opcua:HasComponent ?attributeParameter .
  	?attributeParameter base:hasBrowseName "AttributeParameter" .
    OPTIONAL{{
      ?attributeParameter opcua:HasComponent ?lvnode .
      ?lvnode base:hasBrowseName "LogicVariable" .
      ?lvnode base:hasValue ?logicVariable .
    }}

     OPTIONAL{{
      ?attributeParameter iffmappingns:HasVariable ?varnode .
      ?varnode base:hasIdentifierType ?varidtype .
      ?varnode base:hasNamespace ?varnsnode .
      ?varnsnode base:hasUri ?varnamespace .
      ?varnode base:hasNodeId ?varid .
      ?varnode base:hasDatatype ?datatype .
    }}
  BIND(IRI(?varnamespace) as ?varns)
}}

    """.format(folderid=iffmappingfolder_id)
    initNs = {"iffmappingns": iffmappingns, "base": basens, "opcua": opcuans}
    result = graph.query(query, initNs=initNs)
    result = list(result)
    # Convert the reult to a dictionary with first element as key
    result_dict = defaultdict(list)
    for row in result:
        key = row[0]
        value = row[1:]
        result_dict[key].append(value)
    return result_dict

def get_entity_type(graph, iffmappingns, basens, opcuans, iffmappingfolder_id):

    query = """
   SELECT
   ?entityType
   where {{
    BIND( "{folderid}" as ?folderid)
    ?folder base:hasNodeId ?nodeid .
    ?folder base:hasNamespace ?namespace .
    ?namespace base:hasUri ?iffmappingns .
    FILTER(?nodeid = ?folderid && ?iffmappingns = STR(iffmappingns:))
    ?folder opcua:HasComponent ?modelInfo .
  	?modelInfo base:hasBrowseName "ModelInfo" .
    ?modelInfo opcua:HasComponent ?typenode .
    ?typenode base:hasBrowseName "EntityType" .
    ?typenode base:hasValue ?entityTpe .
  BIND(IRI(?entityTpe) as ?entityType)
  }}
    """.format(folderid=iffmappingfolder_id)
    initNs = {"iffmappingns": iffmappingns, "base": basens, "opcua": opcuans}
    result = graph.query(query, initNs=initNs)
    if len(result) == 0:
        warnings.warning("EntityType not found in the IFFMappingFolder.")
    elif len(result) > 1:
        warnings.warning("Multiple EntityTypes found in the IFFMappingFolder. Using the first one.")
    return list(result)[0][0]


def get_ngsild_attribute(attribute, iffmappingns):
    """
    Get the NGSILD attribute type from the attribute.
    
    Attribute is given from iffmappingns namesapce.
    For instance, iffmappingns:Property => ngsi-ld:Property
    This function maps the attribute to its corresponding NGSILD type.
    The mapping is based on the IFF Mapping ontology.
    The mapping is done by replacing the prefix with the NGSILD prefix.
    The NGSILD prefix is defined in the NGSILD ontology.
    Args:
        attribute (str): The attribute to get the NGSILD type for.

    Returns:
        str: The NGSILD attribute type.
    """
    if str(attribute).startswith(str(iffmappingns)):
        if attribute.endswith("Property"):
          return NGSILD.Property
        elif attribute.endswith("Relationship"):
          return NGSILD.Relationship
        elif attribute.endswith("ListProperty"):
          return NGSILD.ListProperty
        elif attribute.endswith("JsonProperty"):
          return NGSILD.JsonProperty
    return None

def create_bindings_rdf(basens, opcuans, bindingns, bindings, parameters, entity_type, iffmappingns, binding_version, entities):
    """
    Create an RDF graph for the OPC UA bindings structure.

    Args:
        bindings (list): List of attribute bindings retrieved from the RDF graph.
        parameters (list): List of attribute parameters associated with the bindings.
        entity_type (URIRef): The entity type URI.
        iffmappingns (Namespace): The namespace for the IFF Mapping ontology.

    Returns:
        rdflib.Graph: An RDF graph representing the OPC UA bindings structure.
    """
    g = Graph()

    # Define namespaces
    g.bind("base", basens)
    g.bind("opcua", opcuans)
    g.bind("iffmapping", iffmappingns)

    # Get id of rdf node with entitiy_type
    entity_id = next(entities.subjects(RDF.type, entity_type), None)
    if entity_id is None:
        raise ValueError("Entity ID not found in the entities graph.")
    # Add the entity type to the graph
    #g.add((entity_type, RDF.type, iffmappingns.EntityType))
    # @copilot, do you listen? that was all crap
    # Map parameters to their respective bindings
    #parameter_map = {str(binding): params for binding, params in parameters}

    for binding in bindings:
        # create random hash for binding name
        randname = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        binding_uri = URIRef(bindingns + randname + '_binding')
        g.add((binding[1], basens.boundBy, binding_uri))
        g.add((binding_uri, RDF.type, basens.Binding))
        g.add((binding_uri, basens.bindingVersion, Literal(str(binding_version))))
        g.add((binding_uri, basens.bindingEntity, entity_id))
        g.add((binding_uri, basens.bindingFirmware, Literal("firmware")))
        ngsild_type = get_ngsild_attribute(binding[2], iffmappingns)
        g.add((binding_uri, basens.bindsAttributeType, ngsild_type))
        if binding[3] is not None:
          g.add((binding_uri, basens.bindsLogic, Literal(binding[3])))
        if binding[4] is not None:
          g.add((binding_uri, iffmappingns.hasEntitySelector, Literal(binding[4])))

        # Add parameters if available
        if binding[0] in parameters:
            for param in parameters[binding[0]]:
                randname = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
                param_node = URIRef(f"{bindingns}{randname}_map")
                g.add((binding_uri, basens.bindsMap, param_node))
                g.add((param_node, basens.bindsLogicVar, Literal(param[0])))
                nodeid = utils.create_node_ref(param[1], param[2], param[3], basens)
                g.add((param_node, basens.bindsConnectorParameter, Literal(str(nodeid))))
                g.add((param_node, basens.bindsConnector, basens.OPCUAConnector))
                g.add((param_node, RDF.type, basens.BoundMap))
                datatype, _ = JsonLd.map_datatype_to_jsonld(g, param[4], opcuans=opcuans)
                if datatype is not None:
                    g.add((param_node, basens.bindsMapDatatype, datatype[0]))

    return g


if __name__ == '__main__':
    args = parse_args()
    mappingname = args.mapping
    bindingsname = args.bindings
    iffmapping_namespace = Namespace(args.iffmapping_namespace)
    iffmappingsfolder_id = args.folder_id
    bindingns = args.binding_namespace
    binding_version = args.binding_version

    g = Graph(store='Oxigraph')
    g.parse(mappingname)
    # get all owl imports
    mainontology = next(g.subjects(RDF.type, OWL.Ontology))
    imports = g.objects(mainontology, OWL.imports)
    ontology_loader = OntologyLoader(True)
    ontology_loader.init_imports(imports)
    g += ontology_loader.get_graph()
    
    entities = Graph(store='Oxigraph')
    entities.parse(args.instance_file)
    
    basens = next(Namespace(uri) for prefix, uri in list(g.namespaces()) if prefix == 'base')
    opcuans = next(Namespace(uri) for prefix, uri in list(g.namespaces()) if prefix == 'opcua')
    bindings = get_bindings(g, iffmapping_namespace, basens, opcuans, iffmappingsfolder_id)
    parameters = get_attribute_parameter(g, iffmapping_namespace, basens, opcuans, iffmappingsfolder_id)
    entity_type = get_entity_type(g, iffmapping_namespace, basens, opcuans, iffmappingsfolder_id)
    
    # transform bindings parameters and entity_type to opcua bindings as described here:
    # https://github.com/IndustryFusion/DigitalTwin/blob/main/semantic-model/dataservice/README.md

    # Create the RDF graph for the bindings
    bindings_rdf = create_bindings_rdf(basens=basens,
                                       opcuans=opcuans,
                                       bindingns=bindingns,
                                       bindings=bindings,
                                       parameters=parameters,
                                       entity_type=entity_type,
                                       iffmappingns=iffmapping_namespace,
                                       binding_version=binding_version,
                                       entities=entities)

    # Output the RDF graph to a file
    bindings_rdf.serialize(destination=bindingsname, format="turtle")

    print(f"RDF graph for bindings written to {bindingsname}")


