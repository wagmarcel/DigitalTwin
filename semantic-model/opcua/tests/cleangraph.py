import argparse
from rdflib import Graph, Namespace

def main(input_file, output_file):
    # Define the base namespace
    BASE = Namespace("https://industryfusion.github.io/contexts/ontology/v0/base/")

    # Create an RDF graph
    g = Graph()

    # Parse the input file
    g.parse(input_file, format="turtle")

    # Filter out all triples with predicate base:hasValueNode
    triples_to_remove = [(s, p, o) for s, p, o in g if p == BASE.hasValueNode or 
                         o == BASE.ValueNode or 
                         p == BASE.hasEnumValue or
                         p == BASE.hasValueClass]
    for triple in triples_to_remove:
        g.remove(triple)

    # Serialize the modified graph to a new Turtle file
    g.serialize(destination=output_file, format="turtle")

    print(f"Filtered graph saved to {output_file}")

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Filter and remove triples with base:hasValueNode predicate from a Turtle file.")
    parser.add_argument("input_file", type=str, help="Path to the input Turtle file")
    parser.add_argument("output_file", type=str, help="Path to the output Turtle file")

    args = parser.parse_args()
    
    main(args.input_file, args.output_file)
