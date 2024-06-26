import os
import traceback
import os
from urllib.parse import urlparse, urlunparse

import requests
import json
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, jsonify, make_response, session, render_template_string
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)
from azure.storage.blob import BlobServiceClient
import PyPDF2
import jwt
from functools import wraps
from flask import Flask, request, jsonify
import os
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory

load_dotenv()

app = Flask(__name__)

app.secret_key = os.urandom(24)

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


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    return response


@app.route('/redirected')
def redirected():
    # Get the token from the query parameters
    session_cookie = request.headers.get('Cookie')
    session_cookie = session_cookie[session_cookie.find('session') + 8:] if session_cookie else None
    if session_cookie:
        # Set session cookie
        session['session'] = session_cookie

        # Redirect to a temporary page with JavaScript to remove the fragment identifier
        return render_template_string("""
            <script>
            // Function to remove fragment identifier from the URL
            function removeFragmentIdentifier() {
                if (window.location.hash && window.location.hash === '#access_token') {
                    history.replaceState({}, document.title, window.location.pathname + window.location.search);
                }
            }

            // Call the function to remove the fragment identifier
            removeFragmentIdentifier();

            // Redirect to the original redirect URL without the fragment identifier
            window.location.replace("http://localhost:5173/");
            </script>
        """)
    else:
        return redirect(
            "https://readerlogin.b2clogin.com/readerlogin.onmicrosoft.com/oauth2/v2.0/authorize?p=B2C_1_signupsignintest2&client_id=7ae0133c-788a-4466-883f-cc089edc8ab4&nonce=defaultNonce&redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Fredirected&scope=openid&response_type=id_token&prompt=login",
            code=302)


# return render_template('redirected.html')


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


@app.route('/check-authentication')
def check_authentication():
    return jsonify({'isAuthenticated': True}), 200
    # if 'session' in session:
    #     return jsonify({'isAuthenticated': True}), 200
    # else:
    #     return jsonify({'isAuthenticated': False}), 200


@app.route('/logout')
def logout():
    session.pop('session', None)
    return jsonify({'message': 'Successfully logged out'})


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

    upload_path = os.path.join("uploads", file_name)
    if os.path.exists(upload_path) is False:
        with open(upload_path, 'wb') as file:
            file.write(file_content)

    # Create a PDF reader object from the provided content
    text_content = ""
    pdf_reader = PyPDF2.PdfReader(f"uploads//{file_name}")
    for page in pdf_reader.pages:
        text_content += page.extract_text()

    response = make_response('File uploaded successfully', 200)
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    response.data = text_content
    return response


API_ENDPOINT = str(os.environ.get('CONTENT_SAFETY_ENDPOINT'))
API_KEY = str(os.environ.get('CONTENT_SAFETY_KEY'))


@app.route('/check-content-safety', methods=['POST'])
def check_content_safety():
    if 'file' not in request.files:
        response = make_response('No file part', 400)
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        return response

    file = request.files['file']
    file_name = file.filename

    blob_client = blob_container_client.get_blob_client(file_name)
    file_content = blob_client.download_blob().readall()

    upload_path = os.path.join("uploads", file_name)
    if os.path.exists(upload_path) is False:
        with open(upload_path, 'wb') as file:
            file.write(file_content)

    # Create a PDF reader object from the provided content
    text = ""
    pdf_reader = PyPDF2.PdfReader(f"uploads//{file_name}")
    for page in pdf_reader.pages:
        text += page.extract_text()

    treshold = 0.1
    # Define the request headers
    client = ContentSafetyClient(API_ENDPOINT, AzureKeyCredential(API_KEY))

    # Contruct request
    request1 = AnalyzeTextOptions(text="Your input text")

    # Analyze text
    try:
        response = client.analyze_text(request1)
    except HttpResponseError as e:
        if e.error:
            print(f"Error code: {e.error.code}")
            print(f"Error message: {e.error.message}")
            raise

        message = 'Analyze text failed.'
        print(message, e)
        return jsonify(error=message)

    hate_result = next(item for item in response.categories_analysis if item.category == TextCategory.HATE)
    self_harm_result = next(item for item in response.categories_analysis if item.category == TextCategory.SELF_HARM)
    sexual_result = next(item for item in response.categories_analysis if item.category == TextCategory.SEXUAL)
    violence_result = next(item for item in response.categories_analysis if item.category == TextCategory.VIOLENCE)

    if hate_result:
        if hate_result.severity > treshold:
            return jsonify({'isSafe': False}), 200
    if self_harm_result:
        if self_harm_result.severity > treshold:
            return jsonify({'isSafe': False}), 200
    if sexual_result:
        if sexual_result.severity > treshold:
            return jsonify({'isSafe': False}), 200
    if violence_result:
        if violence_result.severity > treshold:
            return jsonify({'isSafe': False}), 200
    return jsonify({'isSafe': True}), 200


if __name__ == '__main__':
    app.run()
