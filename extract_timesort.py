import json
import requests
from py2neo import Graph, Node, Relationship

def fetch_transactions(address):
    url = f"https://mempool.space/testnet/api/address/{address}/txs/chain"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def extract_addresses(transactions):
    result = []
    for tx in transactions:
        input_addresses = [vin["prevout"]["scriptpubkey_address"] for vin in tx["vin"]]
        output_addresses = [vout["scriptpubkey_address"] for vout in tx["vout"]]
        block_time = tx["status"]["block_time"]

        result.append({
            "inputs": input_addresses,
            "outputs": output_addresses,
            "block_time": block_time
        })

    return sorted(result, key=lambda x: x["block_time"])

def insert_into_neo4j(transactions, graph):
    order_counter = 1
    for tx in transactions:
        for input_address in tx["inputs"]:
            input_node = Node("Address", address=input_address, order_number=order_counter)
            graph.merge(input_node, "Address", "address")

            for output_address in tx["outputs"]:
                output_node = Node("Address", address=output_address, order_number=order_counter)
                graph.merge(output_node, "Address", "address")
                graph.create(Relationship(input_node, "SENT", output_node))

        order_counter += 1

def populate_graph(address, depth=3, visited=None, graph=None):
    if visited is None:
        visited = set()
    if graph is None:
        graph = Graph("bolt://localhost:7687", auth=("neo4j", "exegol4thewin"))
	# Mettez vos  creds neo4j
    if address in visited or depth == 0:
        return

    visited.add(address)
    transactions = fetch_transactions(address)
    addresses = extract_addresses(transactions)
    insert_into_neo4j(addresses, graph)

    new_addresses = set()
    for tx in addresses:
        new_addresses.update(tx["inputs"])
        new_addresses.update(tx["outputs"])

    for new_address in new_addresses:
        populate_graph(new_address, depth - 1, visited, graph)

if __name__ == "__main__":
    start_adress = "tb1qgsjgk94yt7mkc9tga4m066ldhxncvuqz8ufupy"
    populate_graph(start_adress)
    print("Données insérées dans Neo4j avec succès !")

