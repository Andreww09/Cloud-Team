import os
import traceback
import os
import requests
import json
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, jsonify, make_response
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)
from azure.storage.blob import BlobServiceClient

load_dotenv()


app = Flask(__name__)
blob_service_client = BlobServiceClient.from_connection_string(str(os.environ.get('CONNECTION_STRING')))
blob_container_client = blob_service_client.get_container_client(str(os.environ.get('CONTAINER_NAME')))


@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/hello', methods=['POST'])
def hello():
    name = request.form.get('name')

    if name:
        print('Request for hello page received with name=%s' % name)
        return render_template('hello.html', name=name)
    else:
        print('Request for hello page received with no name or blank name -- redirecting')
        return redirect(url_for('index'))


@app.route('/reader')
def reader():
    return render_template('reader.html')


@app.route('/options')
def options():
    'Show the options page'
    return render_template('options.html')


@app.route('/GetTokenAndSubdomain', methods=['GET'])
def getTokenAndSubdomain():
    'Get the access token'
    if request.method == 'GET':
        try:
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            data = {
                'client_id': str(os.environ.get('CLIENT_ID')),
                'client_secret': str(os.environ.get('CLIENT_SECRET')),
                'resource': 'https://cognitiveservices.azure.com/',
                'grant_type': 'client_credentials'
            }

            resp = requests.post('https://login.windows.net/' + str(os.environ.get('TENANT_ID')) + '/oauth2/token',
                                 data=data, headers=headers)
            jsonResp = resp.json()

            if ('access_token' not in jsonResp):
                print(jsonResp)
                raise Exception('AAD Authentication error')

            token = jsonResp['access_token']
            subdomain = str(os.environ.get('SUBDOMAIN'))

            return jsonify(token=token, subdomain=subdomain)
        except Exception as e:
            message = 'Unable to acquire Azure AD token. Check the debugger for more information.'
            print(message, e)
            return jsonify(error=message)



@app.route('/upload', methods=['POST'])
def upload():
    # Check if the post request has the file part
    if 'file' not in request.files:
        response = make_response('No file part', 400)
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        return response

    file = request.files['file']

    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        response = make_response('No selected file', 400)
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        return response

    # If the file is present and valid, you can access its properties like filename
    if file:
        filename = file.filename

        # Save the file to disk
        file.save(os.path.join('uploads', filename))

        # Process the file as needed, here just printing the information
        content_type = file.content_type
        file_size = os.path.getsize(os.path.join('uploads', filename))

        print(f"Received file: {filename}, Content-Type: {content_type}, Size: {file_size} bytes")

        # You can perform further processing here, such as parsing the file contents, analyzing, etc.

        # Add CORS header
        response = make_response('File uploaded successfully', 200)
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        return response

    response = make_response('Error in file upload', 500)
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    return response

@app.route('/list-default-stories')
def list_files():
    # Retrieve a list of blob names in the container
    blob_list = blob_container_client.list_blobs()
    file_names = [blob.name for blob in blob_list]
    return jsonify(file_names)

@app.route('/file/<file_name>')
def get_file(file_name):
    # Retrieve a specific blob (file) from the container
    blob_client = blob_container_client.get_blob_client(file_name)
    file_content = blob_client.download_blob().readall()
    return file_content

if __name__ == '__main__':
    app.run()