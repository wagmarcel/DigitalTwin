import rdflib
import argparse

def load_ttl_and_query(ttl_file, sparql_query_file):
    # Initialize an RDF graph
    graph = rdflib.Graph()

    # Load the Turtle file into the graph
    graph.parse(ttl_file, format="ttl")

    # Extract namespaces from the graph
    init_ns = {prefix: rdflib.Namespace(ns) for prefix, ns in graph.namespaces()}

    # Load the SPARQL query from the file
    with open(sparql_query_file, "r") as f:
        sparql_query = f.read()

    # Execute the SPARQL query against the graph with initial namespaces
    results = graph.query(sparql_query, initNs=init_ns)

    # Write the results to stdout
    for row in results:
        print(row)

    if not results:
        print("No results found.")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Apply a SPARQL query to a Turtle file and output the results.")
    parser.add_argument("ttl_file", help="The path to the Turtle (.ttl) file")
    parser.add_argument("sparql_query_file", help="The path to the SPARQL query file")

    # Parse the arguments
    args = parser.parse_args()

    # Load the TTL and SPARQL query, and execute
    load_ttl_and_query(args.ttl_file, args.sparql_query_file)

if __name__ == "__main__":
    main()
