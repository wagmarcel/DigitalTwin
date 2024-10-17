#
# Copyright (c) 2024 Intel Corporation
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
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, SH
import argparse
import lib.utils as utils
from lib.utils import RdfUtils
from lib.bindings import Bindings
from lib.jsonld import JsonLd
from lib.entity import Entity
from lib.shacl import Shacl


attribute_prefix = 'has'

query_namespaces = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?uri ?prefix ?ns WHERE {
    ?ns rdf:type base:Namespace .
    ?ns base:hasUri ?uri .
    ?ns base:hasPrefix ?prefix .
}
"""

query_subclasses = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

CONSTRUCT {
  ?subclass rdfs:subClassOf ?superclass .
  ?subclass a owl:Class .
  ?superclass a owl:Class .
}
WHERE {
  ?subclass rdfs:subClassOf* <http://opcfoundation.org/UA/BaseObjectType> .
  ?subclass rdfs:subClassOf ?superclass .

  # Ensure both subclasses and superclasses are marked as owl:Class
  {
    ?subclass a owl:Class .
  } UNION {
    ?superclass a owl:Class .
  }
}
"""


randnamelength = 16
modelling_nodeid_optional = 80
modelling_nodeid_mandatory = 78
modelling_nodeid_optional_array = 11508
entity_ontology_prefix = 'uaentity'
basic_types = [
    'String',
    'Boolean',
    'Byte',
    'SByte',
    'Int16',
    'UInt16',
    'Int32',
    'UInt32',
    'Uin64',
    'Int64',
    'Float',
    'DateTime',
    'Guid',
    'ByteString',
    'Double'
]
workaround_instances = ['http://opcfoundation.org/UA/DI/FunctionalGroupType', 'http://opcfoundation.org/UA/FolderType']
datasetid_urn = 'urn:iff:datasetId'


def parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='\
parse nodeset instance and create ngsi-ld model')

    parser.add_argument('instance', help='Path to the instance nodeset2 file.')
    parser.add_argument('-t', '--type',
                        help='Type of root object, e.g. http://opcfoundation.org/UA/Pumps/',
                        required=True)
    parser.add_argument('-j', '--jsonld',
                        help='Filename of jsonld output file',
                        required=False,
                        default='instances.jsonld')
    parser.add_argument('-e', '--entities',
                        help='Filename of entities output file',
                        required=False,
                        default='entities.ttl')
    parser.add_argument('-s', '--shacl',
                        help='Filename of SHACL output file',
                        required=False,
                        default='shacl.ttl')
    parser.add_argument('-b', '--bindings',
                        help='Filename of bindings output file',
                        required=False,
                        default='bindings.ttl')
    parser.add_argument('-c', '--context',
                        help='Filename of JSONLD context output file',
                        required=False,
                        default='context.jsonld')
    parser.add_argument('-d', '--debug',
                        help='Add additional debug info to structure (e.g. for better SHACL debug)',
                        required=False,
                        action='store_true')
    parser.add_argument('-m', '--minimalshacl',
                        help='Remove all not monitored/updated shacl nodes',
                        required=False,
                        action='store_true')
    parser.add_argument('-n', '--namespace', help='Namespace prefix for entities, SHACL and JSON-LD', required=True)
    parser.add_argument('-i', '--id',
                        help='ID prefix of object. The ID for every object is generated by "urn:<prefix>:nodeId"',
                        required=False,
                        default="testid")
    parser.add_argument('-xe', '--entity-namespace',
                        help='Overwrite Namespace for entities (which is otherwise derived from <namespace>/entity)',
                        required=False)
    parser.add_argument('-xc', '--context-url', help='Context URL',
                        default="https://industryfusion.github.io/contexts/staging/opcua/v0.1/context.jsonld",
                        required=False)
    parser.add_argument('-xp', '--entity-prefix',
                        help='prefix in context for entities',
                        default="uaentity",
                        required=False)
    parsed_args = parser.parse_args(args)
    return parsed_args


basens = None  # Will be defined by the imported ontologies
opcuans = None  # dito
ngsildns = Namespace('https://uri.etsi.org/ngsi-ld/')


def check_object_consistency(instancetype, attribute_path, classtype):
    needed_superclass = None
    property = shaclg._get_property(instancetype, attribute_path)
    if property is None:
        e.add_instancetype(instancetype, attribute_path)
        e.add_type(classtype)
        return False, None
    shclass = shaclg._get_shclass_from_property(property)
    if shclass != classtype:
        print(f"Warning: Potential inconsistency: {instancetype} => {attribute_path} => \
{shclass} vs {instancetype} => {attribute_path} => {classtype}.")
        common_superclass = utils.get_common_supertype(g, shclass, classtype)
        print(f"Warning: Replacing both classes by common supertype {common_superclass}. This is typcially an \
artefact of using FolderType and \
FunctionalGroupTypes in many places but having same attribute name with different types. TODO: Check whether \
{classtype} or {shclass} SHAPES can be removed.")
        shaclg.update_shclass_in_property(property, common_superclass)
        if common_superclass != classtype and common_superclass != shclass:
            print(f"Warning: common_superclass is neither of {classtype} and {shclass}. This is not yet implemented.")
            needed_superclass = common_superclass
    return True, needed_superclass


def check_variable_consistency(instancetype, attribute_path, classtype):
    if shaclg.attribute_is_indomain(instancetype, attribute_path):
        return True
    e.add_instancetype(instancetype, attribute_path)
    e.add_type(classtype)
    return False


def scan_type(node, instancetype):

    generic_references = rdfutils.get_generic_references(g, node)
    # Loop through all supertypes
    supertypes = rdfutils.get_all_supertypes(g, instancetype, node)

    # Loop through all components
    shapename = shaclg.create_shacl_type(instancetype)
    has_components = False
    for (curtype, curnode) in supertypes:
        components = g.triples((curnode, basens['hasComponent'], None))
        for (_, _, o) in components:
            has_components = scan_type_recursive(o, curnode, instancetype, shapename) or has_components
        addins = g.triples((curnode, basens['hasAddIn'], None))
        for (_, _, o) in addins:
            has_components = scan_type_recursive(o, curnode, instancetype, shapename) or has_components
        organizes = g.triples((curnode, basens['organizes'], None))
        for (_, _, o) in organizes:
            scan_type_nonrecursive(o, curnode, instancetype, shapename)
            has_components = True
        for generic_reference, o in generic_references:
            if generic_reference not in ignored_references:
                has_components = scan_type_nonrecursive(o, curnode, instancetype, shapename,
                                                        generic_reference) or has_components
    return has_components


def scan_type_recursive(o, node, instancetype, shapename):
    has_components = False
    shacl_rule = {}
    browse_name = next(g.objects(o, basens['hasBrowseName']))
    nodeclass, classtype = rdfutils.get_type(g, o)
    if nodeclass == opcuans['MethodNodeClass']:
        return False

    # If defnition is self referential, stop recursion
    if str(instancetype) == str(classtype):
        return False

    attributename = urllib.parse.quote(f'{browse_name}')
    rdfutils.get_modelling_rule(g, o, shacl_rule, instancetype)

    placeholder_pattern = None
    decoded_attributename = urllib.parse.unquote(attributename)
    if utils.contains_both_angle_brackets(decoded_attributename):
        decoded_attributename, placeholder_pattern = utils.normalize_angle_bracket_name(decoded_attributename)
    attributename = urllib.parse.quote(f'{attribute_prefix}{decoded_attributename}')
    if len(decoded_attributename) == 0:  # full template, ignore it
        raise Exception(f"Unexpected attributename {attributename}")
    shacl_rule['path'] = entity_namespace[attributename]

    if rdfutils.isObjectNodeClass(nodeclass):
        stop_scan, _ = check_object_consistency(instancetype, entity_namespace[attributename], classtype)
        if stop_scan:
            return True
        shacl_rule['is_property'] = False
        _, use_instance_declaration = rdfutils.get_modelling_rule(g, o, None, instancetype)
        if use_instance_declaration:
            # This information mixes two details
            # 1. Use the instance declaration and not the object for instantiation
            # 2. It could be zero or more instances (i.e. and array)
            shacl_rule['array'] = True
            _, typeiri = rdfutils.get_type(g, o)
            try:
                typenode = next(g.subjects(basens['definesType'], typeiri))
                o = typenode
            except:
                pass
        components_found = scan_type(o, classtype)
        if components_found:
            has_components = True
            shacl_rule['contentclass'] = classtype
            shaclg.create_shacl_property(shapename, shacl_rule['path'], shacl_rule['optional'], shacl_rule['array'],
                                         False, True, shacl_rule['contentclass'], None, is_subcomponent=True, placeholder_pattern=placeholder_pattern)
    elif rdfutils.isVariableNodeClass(nodeclass):
        stop_scan = check_variable_consistency(instancetype, entity_namespace[attributename], classtype)
        if stop_scan:
            return True
        has_components = True
        try:
            isAbstract = next(g.objects(classtype, basens['isAbstract']))
        except:
            isAbstract = False
        if isAbstract:
            return False
        shacl_rule['is_property'] = True
        shaclg.get_shacl_iri_and_contentclass(g, o, shacl_rule)
        shaclg.create_shacl_property(shapename, shacl_rule['path'], shacl_rule['optional'], shacl_rule['array'],
                                     True, shacl_rule['is_iri'], shacl_rule['contentclass'], shacl_rule['datatype'])
        e.add_enum_class(g, shacl_rule['contentclass'])
    return has_components


def scan_type_nonrecursive(o, node, instancetype, shapename, generic_reference=None):
    shacl_rule = {}
    browse_name = next(g.objects(o, basens['hasBrowseName']))
    nodeclass, classtype = rdfutils.get_type(g, o)
    attributename = urllib.parse.quote(f'has{browse_name}')

    full_attribute_name = entity_namespace[attributename]
    if generic_reference is not None:
        full_attribute_name = generic_reference
    shacl_rule['path'] = full_attribute_name
    if shaclg.attribute_is_indomain(instancetype, full_attribute_name):
        return False
    rdfutils.get_modelling_rule(g, node, shacl_rule, instancetype)
    e.add_instancetype(instancetype, full_attribute_name)
    e.add_type(classtype)

    if rdfutils.isObjectNodeClass(nodeclass) or rdfutils.isObjectTypeNodeClass(nodeclass):
        shacl_rule['is_property'] = False
        shacl_rule['contentclass'] = classtype
        shaclg.create_shacl_property(shapename, shacl_rule['path'], shacl_rule['optional'], False, False,
                                     True, shacl_rule['contentclass'], None)
    elif rdfutils.isVariableNodeClass(nodeclass):
        print(f"Warning: Variable node {o} is target of non-owning reference {full_attribute_name}. \
This will be ignored.")
    return


def scan_entity(node, instancetype, id, optional=False):
    generic_references = rdfutils.get_generic_references(g, node)
    node_id = jsonld.generate_node_id(g, rootentity, node, id)
    instance = {}
    instance['type'] = instancetype
    instance['id'] = node_id
    instance['@context'] = [
        context_url
    ]

    # Loop through all components
    has_components = False
    components = g.triples((node, basens['hasComponent'], None))
    for (_, _, o) in components:
        has_components = scan_entitiy_recursive(node, id, instance, node_id, o) or has_components
    addins = g.triples((node, basens['hasAddIn'], None))
    for (_, _, o) in addins:
        has_components = scan_entitiy_recursive(node, id, instance, node_id, o) or has_components
    organizes = g.triples((node, basens['organizes'], None))
    for (_, _, o) in organizes:
        has_components = scan_entitiy_nonrecursive(node, id, instance, node_id, o) or has_components
    for generic_reference, o in generic_references:
        if generic_reference not in ignored_references:
            has_components = scan_entitiy_nonrecursive(node, id, instance, node_id, o,
                                                       generic_reference) or has_components
    if has_components or not optional:
        jsonld.add_instance(instance)
        return node_id
    else:
        return None


def scan_entitiy_recursive(node, id, instance, node_id, o):
    has_components = False
    shacl_rule = {}
    browse_name = next(g.objects(o, basens['hasBrowseName']))
    nodeclass, classtype = rdfutils.get_type(g, o)
    attributename = urllib.parse.quote(browse_name)

    original_attributename = None
    decoded_attributename = urllib.parse.unquote(attributename)
    optional, array, path = shaclg.get_modelling_rule_and_path(decoded_attributename, URIRef(instance['type']), classtype, attribute_prefix)
    if path is not None:
        original_attributename = decoded_attributename
        decoded_attributename = path.removeprefix(entity_namespace)
        if not path.startswith(str(entity_namespace)):
            print(f"Warning: Mismatch of {entity_namespace} namespace and {path}")
    else:
        decoded_attributename = f'{attribute_prefix}{decoded_attributename}'
    shacl_rule['optional'] = optional
    shacl_rule['array'] = array
    datasetId = None
    
    try:
        is_placeholder = shaclg.is_placeholder(URIRef(instance['type']), entity_namespace[decoded_attributename])
    except:
        is_placeholder = False
    if is_placeholder:
        if original_attributename is None:
            raise Exception(f"No original_attributename given but datasetId neeeded for {decoded_attributename}")
        datasetId = f'{datasetid_urn}:{original_attributename}'
    attributename = urllib.parse.quote(decoded_attributename)
    #shacl_rule['path'] = attributename

    if rdfutils.isObjectNodeClass(nodeclass):
        shacl_rule['is_property'] = False
        relid = scan_entity(o, classtype, id, shacl_rule['optional'])
        if relid is not None:
            has_components = True
            full_attribute_name = f'{entity_ontology_prefix}:{attributename}'
            if instance.get(full_attribute_name) is None:
                instance[full_attribute_name] = []
            attr_instance = {
                'type': 'Relationship',
                'object': relid
            }
            if is_placeholder and datasetId is not None:
                attr_instance['datasetId'] = datasetId
            if debug:
                attr_instance['debug'] = \
                    f'{entity_ontology_prefix}:{attributename}'
            instance[full_attribute_name].append(attr_instance)
            shacl_rule['contentclass'] = classtype
            minshaclg.copy_property_from_shacl(shaclg, instance['type'], entity_namespace[attributename])
        if not shacl_rule['optional']:
            has_components = True
            shacl_rule['contentclass'] = classtype
    elif rdfutils.isVariableNodeClass(nodeclass):
        shacl_rule['is_property'] = True
        shaclg.get_shacl_iri_and_contentclass(g, o, shacl_rule)
        try:
            value = next(g.objects(o, basens['hasValue']))
            if not shacl_rule['is_iri']:
                value = value.toPython()
            else:
                value = e.get_contentclass(shacl_rule['contentclass'], value)

                value = value.toPython()
        except StopIteration:
            if not shacl_rule['is_iri']:
                value = utils.get_default_value(shacl_rule['datatype'])
            else:
                value = e.get_default_contentclass(shacl_rule['contentclass'])
        has_components = True
        if not shacl_rule['is_iri']:
            instance[f'{entity_ontology_prefix}:{attributename}'] = {
                'type': 'Property',
                'value': value
            }
        else:
            instance[f'{entity_ontology_prefix}:{attributename}'] = {
                'type': 'Property',
                'value': {
                    '@id': str(value)
                }
            }
        minshaclg.copy_property_from_shacl(shaclg, instance['type'], entity_namespace[attributename])
        if debug:
            instance[f'{entity_ontology_prefix}:{attributename}']['debug'] = f'{entity_ontology_prefix}:{attributename}'
        try:
            is_updating = bool(next(g.objects(o, basens['isUpdating'])))
        except:
            is_updating = False
        if is_updating or not minimal_shacl:
            bindingsg.create_binding(g, URIRef(node_id), o, entity_namespace[attributename])
    return has_components


def scan_entitiy_nonrecursive(node, id, instance, node_id, o, generic_reference=None):
    has_components = False
    shacl_rule = {}
    browse_name = next(g.objects(o, basens['hasBrowseName']))
    nodeclass, classtype = rdfutils.get_type(g, o)
    attributename = urllib.parse.quote(f'has{browse_name}')
    shacl_rule['path'] = entity_namespace[attributename]
    full_attribute_name = f'{entity_ontology_prefix}:{attributename}'
    if generic_reference is not None:
        full_attribute_name = g.qname(generic_reference)
    if rdfutils.isObjectNodeClass(nodeclass):
        shacl_rule['is_property'] = False
        relid = jsonld.generate_node_id(g, rootentity, o, id)
        if relid is not None:
            has_components = True
            instance[full_attribute_name] = {
                'type': 'Relationship',
                'object': relid
            }
            if debug:
                instance[full_attribute_name]['debug'] = full_attribute_name
            shacl_rule['contentclass'] = classtype
    elif rdfutils.isVariableNodeClass(nodeclass):
        print(f"Warning: Variable node {o} is target of non-owning reference {full_attribute_name}. \
This will be ignored.")
    return has_components


if __name__ == '__main__':

    args = parse_args()
    instancename = args.instance
    rootinstancetype = args.type
    jsonldname = args.jsonld
    entitiesname = args.entities
    shaclname = args.shacl
    bindingsname = args.bindings
    contextname = args.context
    debug = args.debug
    namespace_prefix = args.namespace
    entity_id = args.id
    minimal_shacl = args.minimalshacl
    context_url = args.context_url
    entity_namespace = args.entity_namespace
    entity_prefix = args.entity_prefix

    entity_namespace = Namespace(f'{namespace_prefix}entity/') if entity_namespace is None else entity_namespace
    shacl_namespace = Namespace(f'{namespace_prefix}shacl/')
    binding_namespace = Namespace(f'{namespace_prefix}bindings/')
    entity_ontology_prefix = entity_prefix
    g = Graph(store='Oxigraph')
    g.parse(instancename)
    # get all owl imports
    mainontology = next(g.subjects(RDF.type, OWL.Ontology))
    imports = g.objects(mainontology, OWL.imports)
    for imprt in imports:
        h = Graph(store="Oxigraph")
        print(f'Importing ontology {imprt}')
        h.parse(imprt)
        g += h
        for k, v in list(h.namespaces()):
            g.bind(k, v)

    types = []
    basens = next(Namespace(uri) for prefix, uri in list(g.namespaces()) if prefix == 'base')
    opcuans = next(Namespace(uri) for prefix, uri in list(g.namespaces()) if prefix == 'opcua')
    bindingsg = Bindings(namespace_prefix, basens)
    bindingsg.bind(f'{entity_ontology_prefix}', entity_namespace)
    bindingsg.bind('base', basens)
    bindingsg.bind('binding', binding_namespace)
    shaclg = Shacl(namespace_prefix, basens, opcuans)
    shaclg.bind('shacl', shacl_namespace)
    shaclg.bind('ngsi-ld', ngsildns)
    shaclg.bind('sh', SH)
    shaclg.bind('base', basens)
    minshaclg = Shacl(namespace_prefix, basens, opcuans)
    minshaclg.bind('shacl', shacl_namespace)
    minshaclg.bind('ngsi-ld', ngsildns)
    minshaclg.bind('sh', SH)
    minshaclg.bind('base', basens)
    e = Entity(namespace_prefix, basens, opcuans)
    e.bind('base', basens)
    e.bind(f'{entity_ontology_prefix}', entity_namespace)
    e.bind('ngsi-ld', ngsildns)
    rdfutils = RdfUtils(basens, opcuans)
    e.create_ontolgoy_header(entity_namespace)
    for k, v in list(g.namespaces()):
        e.bind(k, v)
        shaclg.bind(k, v)

    jsonld = JsonLd(basens, opcuans)
    result = g.query(query_namespaces, initNs={'base': basens, 'opcua': opcuans})
    for uri, prefix, _ in result:
        e.bind(prefix, Namespace(uri))
    ignored_references = rdfutils.get_ignored_references(g)

    # First scan the templates to create the rules
    try:
        root = next(g.subjects(basens['definesType'], URIRef(rootinstancetype)))
    except:
        print(f"Error: root-instance with type {rootinstancetype} not found. Please review the type parameter.")
        exit(1)
    scan_type(root, rootinstancetype)
    # Then scan the entity with the real values
    rootentity = next(g.subjects(RDF.type, URIRef(rootinstancetype)))
    scan_entity(rootentity, URIRef(rootinstancetype), entity_id)
    # Add types to entities
    for type in types:
        e.add_subclass(type)
    jsonld.serialize(jsonldname)
    # Add all subclassing to entities
    if entitiesname is not None:
        result = g.query(query_subclasses)
        e.add_subclasses(result)
        e.serialize(destination=entitiesname)
    if shaclname is not None:
        shaclg.serialize(destination=shaclname)
        minshaclg.serialize(destination=f'min_{shaclname}')
    entities_ns = utils.extract_namespaces(e.get_graph())
    shacl_ns = utils.extract_namespaces(shaclg.get_graph())
    combined_namespaces = {**entities_ns, **shacl_ns}
    final_namespaces = {}
    for key, value in combined_namespaces.items():
        final_namespaces[key] = value
    jsonld.dump_context(contextname, final_namespaces)
    if bindingsg.len() > 0:
        bindingsg.serialize(destination=bindingsname)
