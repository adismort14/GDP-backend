from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
# import xml.etree.ElementTree as ET
# import base64
import xmltodict
import os

app = Flask(__name__)

CORS(app) 

port = 8080
github_client_id = os.environ.get('GITHUB_CLIENT_ID')
github_client_secret = os.environ.get('GITHUB_CLIENT_SECRET')

# Get access token
@app.route('/auth/github/access_token', methods=['POST'])
def get_access_token():
    data = request.json
    code = data.get('code')
    try:
        response = requests.post(f"https://github.com/login/oauth/access_token?client_id={github_client_id}&client_secret={github_client_secret}&code={code}")
        parameters = response.text.split('&')
        access_token_parameter = next(param for param in parameters if param.startswith('access_token='))
        access_token = access_token_parameter.split('=')[1]
        return jsonify({'access_token': access_token}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to obtain access token'}), 500

# Get the user repositories
@app.route('/user/repos', methods=['GET'])
def get_user_repositories():
    access_token = request.args.get('access_token')

    if not access_token:
        return jsonify({'error': 'Access token not provided'}), 400

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {access_token}', 
        'X-GitHub-Api-Version': '2022-11-28'
    }

    repositories = []

    url = 'https://api.github.com/user/repos'
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  

        repositories.extend(response.json())

        url = response.links.get('next', {}).get('url')

    return jsonify(repositories)

# Get the project tree and parse it.
@app.route('/repo/dependencies', methods=['GET'])
def get_repo_dependencies():
    repo_owner = request.args.get('ownerName')
    repo_name = request.args.get('repoName')
    access_token = request.args.get('accessToken')

    dir_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents'
    response = requests.get(dir_url, headers={'Authorization': f'BEARER {access_token}'})

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch repository contents'}), 500
    
    dependencies = []
    data = response.json()
    for item in data:
        if item['name'] == 'pom.xml':
            pom_xml_url = item['download_url']
            pom_xml_response = requests.get(pom_xml_url)
            if pom_xml_response.status_code == 200:
                dependencies.extend(parse_pom_xml(pom_xml_response.text))
            else:
                return jsonify({'error': f'Failed to fetch pom.xml file: {item["name"]}'})
    
    return jsonify(dependencies)


def parse_pom_xml(xml_content):
    dependencies = []
    xml_dict = xmltodict.parse(xml_content)
    
    dependencies_list = xml_dict['project'].get('dependencyManagement', {}).get('dependencies', {}).get('dependency', [])
    dependencies_list2 = xml_dict['project'].get('dependencies', {}).get('dependency', [])
    dependencies_list += dependencies_list2
    
    if not isinstance(dependencies_list, list):
        dependencies_list = [dependencies_list]
    
    for dependency in dependencies_list:
        group_id = dependency.get('groupId', 'N/A')
        artifact_id = dependency.get('artifactId', 'N/A')
        version = dependency.get('version', 'N/A')
        
        # handled version pointer here
        if version.startswith("${") and version.endswith("}"):
            properties = xml_dict['project'].get('properties', {})
            new_version = properties.get(version[2:-1], 'N/A')
            if new_version != 'N/A':
                version = new_version
        
        dependencies.append(f'{group_id}: Version {version}')
    
    return dependencies

if __name__ == '__main__':
    app.run(debug=True)
