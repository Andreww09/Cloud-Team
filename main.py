import datetime

from flask import Flask, request, render_template, jsonify
from google.cloud import vision

app = Flask(__name__)
client = vision.ImageAnnotatorClient()


@app.route("/")
def root():
    # For the sake of example, use static information to inflate the template.
    # This will be replaced with real information in later steps.
    dummy_times = [
        datetime.datetime(2018, 1, 1, 10, 0, 0),
        datetime.datetime(2018, 1, 2, 10, 30, 0),
        datetime.datetime(2018, 1, 3, 11, 0, 0),
    ]

    return render_template("index.html", times=dummy_times)


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
