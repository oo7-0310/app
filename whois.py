import sys
import os 
import re
import json
import subprocess

# flaks 
from flask import request, jsonify,Blueprint
from neo4j import GraphDatabase

DOMAIN_PATTERN = r'https?://([^/]+)'

bp = Blueprint('whois', __name__, url_prefix='/whois')
driver = GraphDatabase.driver('bolt://172.25.0.2:7687', auth=('neo4j', 'icheneo4j'))
# Only whois 

@bp.route('/add',methods=['POST'])
def add_domain():
    data = request.get_json()
    uri = data['uri']

    # Print the received data
    print("Received data:", data)

    if not uri:
        return jsonify({'uri':'URI is required'}), 400
    match = re.search(DOMAIN_PATTERN, uri)

    if match:
        match_uri = match.group(1)
        if match_uri:
            session = driver.session()
            # add and make a relation
            query = """
                CREATE (:Domain {domain: $domain})
                """
            params = {
                'domain':match_uri
            }
            result = session.run(query,parameters=params)
            return jsonify({
                'status':'success'
            }), 200

@bp.route('/exec',methods=['POST'])
def exec_whois():
    data = request.get_json()
    uri = data['uri']
    if not uri:
        return jsonify({'uri':'URI is required'}), 400
    
    match = re.search(DOMAIN_PATTERN, uri)
    if match:
        match_uri = match.group(1)
        command = ['./tools/whois-cli/whois','-j' ,match_uri]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            whois_output = result.stdout
            try:
                parsed_data = json.loads(whois_output)
                created_date = parsed_data['domain'].get('created_date')
                reg_name = parsed_data['registrar'].get('name')
                reg_email = parsed_data['registrar'].get('email')

                if created_date and reg_name and reg_email:
                    
                    session = driver.session()
                    # add and make a relation
                    query = """
                        WITH $username AS username, $domain AS domain, $email AS email
                        CREATE (:Email {email: email})
                        CREATE (:Person {name: username})
                        WITH username, domain, email
                        MATCH (d:Domain {domain: domain})
                        MATCH (p:Person {name: username})
                        MATCH (e:Email {email: email})
                        CREATE (d)-[:AC]->(p)
                        CREATE (d)-[:AC_Mail]->(e)
                    """
                    params = {
                        'email':reg_email,
                        'username': reg_name,
                        'domain':match_uri
                    }

                    result = session.run(query,parameters=params)
                    return jsonify({
                        'created_date':created_date,
                        'reg_name':reg_name,
                        'reg_email' : reg_email
                    }), 200
                else:
                    print(
                        f"created_date:{created_date},\n \
                        reg_name:{reg_name},\n \
                        reg_email:{reg_email}"
                    )
                    response_data = {"error":"Some fields are missed."}
                        
            except json.JSONDecodeError as e:
                response_data = {"error": f"Failed to parse JSON: {str(e)}"}
        else:
            error_message = result.stderr
            response_data = {"error": error_message}
    else:
        response_data = {"message": "URI field not found"}

    print(response_data)
    return jsonify(response_data),400

def record_to_dict(record):
    return {
        'nodes': dict(record['n']),
        'relationships': dict(record['r']),
        'targetNode': dict(record['m'])
    }

@bp.route('/graph')
def get_graph():
    try:
        with driver.session() as session:
            result = session.run('MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100')
            print(result)
            data = [record_to_dict(record) for record in result]
            
        return jsonify(data)
    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500

def record_to_dict(record):
    return {
        'nodes': dict(record['n']),
        'relationships': dict(record['r']),
        'targetNode': dict(record['m'])
    }

# @bp.route('/process_data', methods=['POST'])
# def process_data():
#     data = request.get_json()
#     print("Received data:", data)
#     return jsonify({'result': 'success', 'data': data})

            