# Semantic Data of OPCUA


## Conversion of OPCUA Objects to NGSI-LD:
OPCUA:

```
MyRootObject (NodeId: ns=2; i=1000)
 ├── MyXObject (NodeId: ns=2;i=1001)
 ├── MyYObject (NodeId: ns=2;i=1002)
 ├── MyZObject (NodeId: ns=2;i=1003)
```
NGSI-LD:

```
 {
    "id": "urn:mainid:nodei1000",
    "type": "MyArrayObject",
    "MyXObject":{
            "type": "Relationship",
            "object": "urn:mainid:sub:nodei1001"
    },
    "MyYObject":{
            "type": "Relationship",
            "object": "urn:mainid:sub:nodei1002"
    },
    "MyZObject":{
            "type": "Relationship",
            "object": "urn:mainid:sub:nodei1003"
    },
 }
 ```

## Semantic conversion of OPCUA Object-arrays

Objects which are part of an array are typcially defined with a template <> definition. E.g. object_<no> means that there could be object_1, object_2, ... browsepath.
The problem of this is that the name convention is not exactly specified, so object_#1, object#2, ... or object_01, object_02, ... is also possible. Moreover, this makes it difficult to write logic which addresses all element in an array because one needs to guess the names with a pattern. Therefore, we treat this case different. A NGSI-LD instance of such an object would look as follows:

OPCUA:

```
MyArrayObject (NodeId: ns=2; i=1000)
 ├── MyObject_01 (NodeId: ns=2;i=1001)
 ├── MyObject_02 (NodeId: ns=2;i=1002)
 ├── MyObject_03 (NodeId: ns=2;i=1003)
```

 NGSI-LD:

```
 {

    "id": "urn:mainid:nodei1000",
    "type": "MyArrayObject",
    "MyObject": [
        {
            "type": "Relationship",
            "object": "urn:mainid:sub:nodei1001",
            "datasetId": "urn:iff:datasetId:MyObject_01"
        },
        {
            "type": "Relationship",
            "object": "id of MyObject_02",
            "datasetId": "urn:iff:datasetId:MyObject_02"
        },
        {
            "type": "Relationship",
            "object": "id of MyObject_03",
            "datasetId": "urn:iff:datasetId:MyObject_03"
        }
    ]
 }
 ```

 Node that you can now access all objects at once, e.g. with a SHACL expression but still you can select one specific object by using the respective `datasetId` reference or the `id` of the specific object. 

## Input to the semantic conversion
Besides the companion specifications, there are two files needed:
1. A `nodeset2` file which contains the Type Definitions of the machine.
2. A `nodeset2` file which contains a snapshot of the Instance

As a result, there are the following files created:

## `instances.jsonld`

Contains all entities with respective Properties and Relationships of the machine instances.

## `shacl.ttl`

Contains all SHACL rules which could be derived automatically from the Type definition `nodeset2`.

## `entities.ttl`

Contains all generic semantic information related to the entities which could be derived for Relationships and Properties. It also include the type hierarchy.

## `knowledge.ttl`

Contains all information about additional classes e.g. describing enums

# Validation

## Offline Validation

For offline validation one can apply 

    pyshacl -s shacl.ttl -e entities.ttl  -df json-ld instances.jsonld

To demonstrate the need of the entities.ttl, try validation without entities.ttl. Dependent on the models you will see additional errors due to the fact that SHACL validator cannot use the knowledge that one type is a subtype of something else.