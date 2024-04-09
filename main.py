import datetime

from flask import Flask, request, render_template, jsonify
from google.cloud import vision
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token

app = Flask(__name__)
client = vision.ImageAnnotatorClient()

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
        store_time(datetime.datetime.now(tz=datetime.timezone.utc))
        times = fetch_times(10)

    return render_template(
        "index.html", user_data=claims, error_message=error_message, times=times
    )


@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    image_content = file.read()
    image = vision.Image(content=image_content)

    # Perform label detection on the image
    response = client.label_detection(image=image)

    # Process the response and return the results
    labels = [label.description for label in response.label_annotations]
    return jsonify({'labels': labels})


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
