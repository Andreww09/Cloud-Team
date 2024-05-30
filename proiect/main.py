import json
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, make_response
from dotenv import load_dotenv
import os
import requests
from flask_cors import CORS
from google.cloud import language_v1

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
load_dotenv()

# Initialize Firebase Admin SDK
cred = credentials.Certificate("final-project-424823-firebase-adminsdk-2k6qj-36f71e5bb1.json")
firebase_admin.initialize_app(cred)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "final-project-424823-cd4d491fbb3c.json"

# Initialize Firestore DB
db = firestore.client()


def add_search_entry(uid, search_term):
    user_ref = db.collection('users').document(uid)
    search_history_ref = user_ref.collection('search_history')

    search_history_ref.add({
        'search_term': search_term,
        'timestamp': firestore.SERVER_TIMESTAMP
    })


# Function to retrieve search history for a user
@app.route('/get-history', methods=['GET'])
def get_search_history(uid):
    user_ref = db.collection('users').document(uid)
    search_history_ref = user_ref.collection('search_history')

    search_entries = search_history_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()

    response = []
    for entry in search_entries:
        response.append(entry.to_dict())
        # print(f'{entry.id} => {entry.to_dict()}')
    return jsonify(response)


def write_to_json(data, file_name):
    # Writing JSON data to a file
    with open(file_name, 'w') as f:
        json.dump(data, f)


def read_from_json(file_name):
    # Reading JSON data from a file
    with open(file_name, 'r') as f:
        data = json.load(f)
    return data


def find_rating(rating):
    score = 0
    n = len(rating)
    for i in range(n):
        if rating[i].isdigit():
            if i + 2 < n and rating[i + 1] == '.' and rating[i + 2].isdigit():
                score = float(rating[i:i + 3])
                return score
            else:
                score = int(rating[i])
                return score
    return score


def extract_asin(url):
    search_str = "dp/"
    index = url.find(search_str)

    if index != -1:
        # If "dp/" is found, return the next 10 characters after "dp/"
        start_index = index + len(search_str)
        return url[start_index:start_index + 10]
    else:
        # If "dp/" is not found, return the last 10 characters
        return url[-10:]


# @app.after_request
# def add_cors_headers(response):
#     response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
#     return response


def sentiment_analysis(text):
    client = language_v1.LanguageServiceClient()

    # Text to analyze
    text = "I love the new movie, it's fantastic!"

    # Analyze sentiment
    document = {"content": text, "type": language_v1.Document.Type.PLAIN_TEXT}
    response = client.analyze_sentiment(request={'document': document})
    # Get sentiment score and magnitude
    sentiment = response.document_sentiment
    reviews = []
    for sentence in response.sentences:
        review = {
            'sentence': sentence.text.content,
            'sentiment': sentence.sentiment.score
        }
        reviews.append(review)
    response = {
        'sentiment': sentiment,
        'reviews': reviews
    }
    return response


@app.route('/lookup-product', methods=['GET'])
def look_up_product():
    product_url = request.args.get('url')
    if not product_url:
        return jsonify({"error": "Product URL is required"}), 400
    url = "https://axesso-axesso-amazon-data-service-v1.p.rapidapi.com/amz/amazon-lookup-product"
    asin = extract_asin(product_url)
    new_url = f"amazon.com/dp/{asin}"
    querystring = {"url": new_url}

    headers = {
        "X-RapidAPI-Key": str(os.environ.get('AXESSO_API_KEY')),
        "X-RapidAPI-Host": str(os.environ.get('AXESSO_HOST')),
    }

    # response = requests.get(url, headers=headers, params=querystring)

    # data = response.json()
    # write_to_json(data, 'loop_up_product.json')

    data = read_from_json("loop_up_product.json")
    rating = 0
    rating_count = 0
    reviews_text = ""
    for review in data['reviews']:
        reviews_text += review['text']
        rating += find_rating(review['rating'])
        rating_count += 1
    #     print(review['text'])
    # print(reviews_text)
    analysis = sentiment_analysis(reviews_text)
    response = {
        'score': analysis['sentiment'].score,
        'reviews': analysis['reviews'],
        'rating': rating / rating_count
    }
    return jsonify(response)


def sort_offers_by_price(offers, ascending=True):
    return sorted(offers, key=lambda x: x['price'], reverse=not ascending)


def sort_offers_by_seller_rating(offers, ascending=True):
    return sorted(offers, key=lambda x: x['sellerRating'], reverse=not ascending)


@app.route('/lookup-seller-prices', methods=['GET'])
def look_up_seller_prices():
    product_url = request.args.get('url')
    if not product_url:
        return jsonify({"error": "Product URL is required"}), 400
    asin = extract_asin(product_url)
    sorted_by = request.args.get('sortedBy')
    min_price = request.args.get('minPrice')
    max_price = request.args.get('maxPrice')
    order = request.args.get('order')
    print(asin)

    url = "https://axesso-axesso-amazon-data-service-v1.p.rapidapi.com/v2/amz/amazon-lookup-prices"

    querystring = {"page": "1", "domainCode": "com", "asin": asin}

    headers = {
        "X-RapidAPI-Key": str(os.environ.get('AXESSO_API_KEY')),
        "X-RapidAPI-Host": str(os.environ.get('AXESSO_HOST')),
    }

    # response = requests.get(url, headers=headers, params=querystring)
    #
    # data = response.json()
    # write_to_json(data, 'loop_up_seller_prices.json')

    data = read_from_json("loop_up_seller_prices.json")
    offers = []
    for offer in data['offers']:
        product = {
            "fulfilledBy": offer['fulfilledBy'],
            "price": offer['price'],
            "sellerName": offer['sellerName'],
            "sellerRating": offer['sellerRating'],
            "sellerId": offer['sellerId']
        }
        if min_price and offer['price'] < float(min_price):
            continue
        if max_price and offer['price'] > float(max_price):
            continue
        offers.append(product)

    ascending = True
    if order == "descending":
        ascending = False
    if sorted_by == "rating":
        return sort_offers_by_seller_rating(offers, ascending)
    if sorted_by == "price":
        return sort_offers_by_price(offers, ascending)

    return jsonify(offers)


@app.route('/search-by-keyword', methods=['GET'])
def search_by_keyword():
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"error": "keyword is required"}), 400
    url = "https://axesso-axesso-amazon-data-service-v1.p.rapidapi.com/amz/amazon-search-by-keyword-asin"

    querystring = {"domainCode": "com", "keyword": keyword, "page": "1", "excludeSponsored": "false",
                   "sortBy": "relevanceblender", "withCache": "true"}

    headers = {
        "X-RapidAPI-Key": str(os.environ.get('AXESSO_API_KEY')),
        "X-RapidAPI-Host": str(os.environ.get('AXESSO_HOST')),
    }

    # response = requests.get(url, headers=headers, params=querystring)
    #
    # data = response.json()
    # write_to_json(data, 'search_by_keyword.json')

    data = read_from_json("search_by_keyword.json")
    products = []
    for product in data["searchProductDetails"]:
        info = {
            "image": product['imgUrl'],
            "desciption": product['productDescription'],
            "asin": product['asin'],
            "price": product['price']
        }
        products.append(info)
    return jsonify(products)


if __name__ == '__main__':
    app.run(debug=True)
    # user_id = 'example_uid'

    # Add search entries
    # add_search_entry(user_id, 'python firestore tutorial')
    # add_search_entry(user_id, 'firebase admin sdk python')
    #
    # # Retrieve and print search history
    # get_search_history(user_id)
