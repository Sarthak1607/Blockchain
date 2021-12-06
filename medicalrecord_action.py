from bs4 import BeautifulSoup
# from requests_html import HTMLSession
from urllib.parse import urljoin, urlparse
from flask import Flask, request, session, redirect, render_template, url_for, jsonify
import requests
import datetime
import hashlib
import json
from uuid import uuid4
from tkinter import *
import tkinter.messagebox
# Import modules for CGI handling
# import cgi, cgitb

class BlockChain:
    def __init__(self):
        self.chain=[]
        self.transactions=[]
        self.nodes=set()
        self.create_block(proof=1,previous_hash='0')
        
    def create_block(self,proof,previous_hash):
        block={'index':len(self.chain)+1,
               'timestamp':str(datetime.datetime.now()),
               'proof':proof,
               'previous_hash':previous_hash,
               'transactions':self.transactions
            
            }
        self.transactions=[]
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True 
    
    def add_transaction(self,po_number,po_date,vname,vlname,fname,lname,bill_address,ship_address):
        self.transactions.append({
            "po_number" : po_number, 
            "po_date" : po_date, 
            "vend_name" : vname, 
            "vend_last_name" : vlname, 
            "first_name" : fname,
            "last_name" : lname, 
            "bill_address" : bill_address, 
            "ship_address" : ship_address
            })
        previous_block=self.get_previous_block()
        return previous_block['index']+1
    
    def add_node(self,address):
        parsed_url=urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    ### consensus protocol
    
    def replace_chain(self):
        network=self.nodes
        longest_chain=None
        max_length=len(self.chain)
        
        for node in network:
            response=requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False




app = Flask(__name__)

### creating an address for the node on Port 5000
node_address=str(uuid4()).replace('-','')

### Create The BlockChain
blockchain=BlockChain()


@app.route("/")
def main():
    return render_template("main.html")

# Adding a new transaction to the Blockchain
# @app.route('/add_transaction', methods = ['POST'])
# def add_transaction():
#     json = request.get_json()
#     transaction_keys = ['sender', 'receiver', 'amount']
#     if not all(key in json for key in transaction_keys):
#         return 'Some elements of the transaction are missing', 400
#     index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
#     response = {'message': f'This transaction will be added to Block {index}'}
#     return jsonify(response), 201

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # blockchain.add_transaction(sender = node_address, receiver = 'Krish', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    transaction_chain = {'message': 'The transaction has been added to block and the block has been mined',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return transaction_chain

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return response

@app.route("/fmcg_action", methods = ['POST'])
def po_form():
    po_number = request.form["form_po_num"]
    po_date = request.form["form_po_date"]
    vname = request.form["form_vname"]
    vlname = request.form["form_vlname"]
    fname = request.form["form_fname"]
    lname = request.form["form_lname"]
    bill_address = request.form["form_bill_address"]
    ship_address = request.form["form_ship_address"]
    params = {"po_number" : po_number, "po_date" : po_date, "vend_name" : vname, "vend_last_name" : vlname, 
    "first_name" : fname, "last_name" : lname, "bill_address" : bill_address, "ship_address" : ship_address}
    json = params
    transaction_keys = ['po_number', 'po_date', 'vend_name', 'vend_last_name', 'first_name', 'last_name',
    'bill_address', 'ship_address']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = blockchain.add_transaction(json['po_number'], json['po_date'], json['vend_name'], json['vend_last_name'],
    json['first_name'], json['last_name'], json['bill_address'], json['ship_address'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return redirect(url_for('mine_block'))

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'The Blockchain is not valid.'}
        return response

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = {"nodes": ["http://127.0.0.1:5004",
                    "http://127.0.0.1:5002",
                    "http://127.0.0.1:5003"]
            }
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return response

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return response


if __name__ == "__main__":
  app.run(debug=True)