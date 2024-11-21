# Overview

This document describes how to map OPCUA data into Semantic Web [6] data, more specifically we describe how to transform OPCUA data into the following 3 standards:
1. The **constraints and rules** are expressed in the SHApes Constraint Language (SHACL) [1] (`shacl.ttl`)
2. The **ontology** data about types, enumerations and other explicit knowledge e is expressed in the Web Ontology Language (OWL)[2] (called  `entities.ttl`, or sometimes `knowledge.ttl` or `ontolgoy.ttl`)
3. Representation of the OPCUA **instance** as JSON-LD [3] or more specifically the NGSI-LD[4] standard (called `instances.jsonld`)

The files are all represented in Resource Description Format[6] serialized in the Turtle[5] or JSON-LD.


