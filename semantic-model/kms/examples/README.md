# Q&A Examples

This directory contains "handmade" Q&A examples for the SHACL/JSON-LD based modelling. They are validated with the `validate.bash` script.

## Setup

1. Install and setup the semantic SDK from the IFF/DigitalTwin project.
2. Install `yq` version 4, e.g. on Ubuntu

    `sudo snap install yq --channel=v4/stable`

3. Configure the `TOOLPREFIX` in the validation script to contain the path to the IFF DigitalTwin semantic SDK.

## Structure

The example.yaml files contain a question field and shacl.ttl, model.yaml (in future expect also knowledge.ttl) as answer. The different models represent complient and non-complient NGSI-LD objects according to the SHACL specification.
Example:

```yaml
question:
    Here is my question. Create the SHACL constraints for an object
    provide me 3 examples, model1.jsonld is compliant, model2.jsonld
    contains a too high value.
model1.yaml:
    [
        {
            "@context": "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
            "id": "urn:123",
            "type": "https://example.com/mytype"
        }
    ]
model2.yaml:
    ["not compliant"]
shacl.ttl:
    myshape a sh:NodeShape .

```