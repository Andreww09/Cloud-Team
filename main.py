import datetime

import google.oauth2.id_token
from flask import Flask, render_template, request, url_for
from flask import jsonify
from google.auth.transport import requests
from google.cloud import vision
from google.cloud import storage
import jwt
import os
import json

app = Flask(__name__)
client = vision.ImageAnnotatorClient()
storage_client = storage.Client()

firebase_request_adapter = requests.Request()


@app.route("/")
def root():
    # Verify Firebase auth.
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None

    if id_token:
        try:
            # Verify the token against the Firebase Auth API. This example
            # verifies the token on each page load. For improved performance,
            # some applications may wish to cache results in an encrypted
            # session store (see for instance
            # http://flask.pocoo.org/docs/1.0/quickstart/#sessions).
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as exc:
            # This will be raised if the token is expired or any other
            # verification checks fail.
            error_message = str(exc)

        # Record and fetch the recent times a logged-in user has accessed
        # the site. This is currently shared amongst all users, but will be
        # individualized in a following step.
        # store_time(datetime.datetime.now(tz=datetime.timezone.utc))
        # times = fetch_times(10)

    return render_template(
        "index.html", user_data=claims, error_message=error_message
    )


@app.route("/main.html")
def main():
    return render_template("main.html")


@app.route('/upload', methods=['POST'])
def upload():
    id_token = request.cookies.get("token")
    if id_token:
        # Assuming the user ID is present in the ID token
        user_id = extract_user_id(id_token)  # You need to implement this function to extract user ID from token

        # Check if 'image' is in the request files
        if 'image' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['image']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'})

        image_content = file.read()
        image = vision.Image(content=image_content)

        # Perform label detection on the image
        response = client.label_detection(image=image)

        # Process the response and return the results
        labels = [label.description for label in response.label_annotations]
        # labels = ["a"]
        # Store image and labels in Google Cloud Storage
        upload_image_and_labels(user_id, file, image_content, labels)

        return jsonify({'labels': labels})
    else:
        return jsonify({'error': 'User not authenticated'})


def upload_image_and_labels(user_id, file, image_content, labels):
    # Create a bucket name where you want to store user data
    bucket_name = 'staging.ccteam-419717.appspot.com'
    image_name = '.'.join(file.filename.split('.')[:-1])

    image_blob_name = f'upload/{user_id}/{image_name}/{file.filename}'

    # Create a blob name for the labels (e.g., using JSON format)
    labels_blob_name = f'upload/{user_id}/{image_name}/{os.path.splitext(file.filename)[0]}.json'

    image_bucket = storage_client.bucket(bucket_name)
    image_blob = image_bucket.blob(image_blob_name)
    image_blob.upload_from_string(image_content)

    # Upload the labels to Google Cloud Storage
    labels_bucket = storage_client.bucket(bucket_name)
    labels_blob = labels_bucket.blob(labels_blob_name)
    labels_blob.upload_from_string(json.dumps(labels))


@app.route('/history', methods=['GET'])
def history():
    id_token = request.cookies.get("token")
    if id_token:
        # Assuming the user ID is present in the ID token
        user_id = extract_user_id(id_token)  # You need to implement this function to extract user ID from token

        # Retrieve images and labels for the current user from Google Cloud Storage
        history_data = get_user_history(user_id)
        return jsonify(history_data)
    else:
        return jsonify({'error': 'User not authenticated'})


def get_user_history(user_id):
    # Create a bucket name where user data is stored
    bucket_name = 'staging.ccteam-419717.appspot.com'
    folders = set()  # Set to store unique folder names

    # Get the list of blobs to extract folder names
    for blob in storage_client.list_blobs(bucket_name, prefix=f'upload/{user_id}/'):
        folder = blob.name.split('/')[2]  # Assuming the folder name is the third element after splitting by '/'
        folders.add(folder)

    # Iterate over folders and process the files within each folder
    history_data = []
    for folder in folders:
        # Get the list of blobs within the current folder
        blobs = storage_client.list_blobs(bucket_name, prefix=f'upload/{user_id}/{folder}/')

        # Process the files within the current folder
        image_url = ''
        labels = ''
        for blob in blobs:
            if blob.name.endswith('.json'):  # Assuming labels are stored in JSON files
                labels_data = blob.download_as_string().decode('utf-8')
                labels = json.loads(labels_data)
            if blob.name.lower().endswith(
                    ('.png', '.jpg', '.jpeg', '.gif')):  # Assuming images are stored with these extensions
                print(blob.name)
                image_url = f'https://storage.cloud.google.com/{bucket_name}/{blob.name}'  # URL to the image
                print(image_url)

        history_data.append({'image': image_url, 'labels': labels})
    return history_data


def extract_user_id(id_token):
    try:
        # Decode the ID token
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})

        # Extract and return the user ID from the decoded token
        return decoded_token['user_id']
    except jwt.ExpiredSignatureError:
        # Handle token expiration error
        return None
    except jwt.InvalidTokenError:
        # Handle invalid token error
        return None


if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)
#
# from google.cloud import vision
#
# # Initialize the Vision API client
# client = vision.ImageAnnotatorClient()
#
# # Image URL to analyze
# pics = ['https://i.imgur.com/2EUmDJO.jpg', 'https://i.imgur.com/FPMomNl.png','https://i.imgur.com/ps6iwpg.jpeg']
# image_url=pics[2]
# # Create an Image instance and set the image source
# image = vision.Image()
# image.source.image_uri = image_url
#
# # Perform label detection on the image
# response = client.label_detection(image=image)
#
# # Print detected labels
# print('Labels:')
# for label in response.label_annotations:
#     print(label.description, '(confidence:', label.score, ')')
