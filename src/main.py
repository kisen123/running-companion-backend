from flask import Flask, request, jsonify, url_for
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
import numpy as np
import joblib

import os
import json
from dotenv import load_dotenv

load_dotenv()

MODEL_DIR = "trained_models"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))

@app.route("/get-user/<user_id>", methods=['GET'])
def get_user(user_id):
    
    user_data = {
        "user_id": user_id,
        "name": "John Doe",
        "email": "john.doe@example.com"
    }

    return jsonify(user_data), 200


@app.route("/create-user", methods=['POST'])
def create_user():
    data = request.get_json()

    return jsonify(data), 201



@app.route("/api/images/categories", methods=['GET'])
def get_image_categories():
    base_dir = os.path.join(app.static_folder, 'images')


    if not os.path.isdir(base_dir):
        return jsonify({"error": "Image folders not found"}), 404

    image_categories = [os.path.basename(category) for category in os.listdir(base_dir)]

    # Looping through each category. Each category is a JSON object in the output
    data = []
    image_file_iter = 0
    for i, image_category_name in enumerate(image_categories):

        image_category_path = url_for('static', filename=f'images/{image_category_name}/')
        image_category_file_urls = [image_category_path + file_name for file_name in os.listdir(os.path.join(base_dir, image_category_name))]

        # Filling each category with it's respective image URIs and a unique image ID for each image
        category_image_objects = []
        for image_category_file_url in image_category_file_urls:

            # One 'category_image_object' has a unique image_id, and a URI
            category_image_objects.append({
                "image_id": str(image_file_iter),
                "image_url": f'http://{os.getenv("computer_LAN_IP")}:{os.getenv("host_port")}' + image_category_file_url
            })

            image_file_iter += 1

        # Appending each folder's files to an output data object
        data.append({
            "category_id": str(i + 1),
            "image_category": image_category_name,
            "images": category_image_objects
        })



    return jsonify(data), 200




@app.route("/api/images/<category>", methods=['GET'])
def get_images_per_category(category):
    base_dir = os.path.join(app.static_folder, 'images', category)

    if not os.path.isdir(base_dir):
        return jsonify({"error": "Category not found"}), 404
    

    image_files = [f for f in os.listdir(base_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    data = []

    for i, filename in enumerate(image_files):
        image_url = url_for('static', filename=f'images/{category}/{filename}')

        data.append({
            "id": str(i + 1),
            "uri": f'http://{os.getenv("computer_LAN_IP")}:{os.getenv("host_port")}' + image_url
        })

    return jsonify(data), 200



@app.route("/api/training_data", methods=['POST'])
def update_training_data():
    message = ""
    data = request.get_json()

    # Checking if a training data file exists. If not, we create one
    training_data_exists = os.path.exists("training_data.json")
    if not training_data_exists:
        with open("training_data.json", "w") as file:
            json.dump({"training_data": []}, file)
            message += "Training data file created, as it did not previously exist.\t"

    # Loading the existing training data
    with open("training_data.json", "r") as file:
        training_data = json.load(file)


    # Updating the training data with the new data
    if "training_data" in data:
        try:
            training_data["training_data"].append(data["training_data"])
            message += "Training data updated successfully.\t"

            # Saving the updated training data back to the file
            with open("training_data.json", "w") as file:
                json.dump(training_data, file, indent=4)

        except KeyError:
            return jsonify({"error": "Invalid data format. 'training_data' key is required."}), 400
    
    
    # Here you would typically process the training data
    return jsonify({"message": "Training data received", "data": data}), 200



@app.route("/api/inference_model", methods=['POST'])
def inference_ml_model():
    if not os.path.exists(MODEL_DIR):
        return jsonify({"error": "No trained models found."}), 404

    features = request.get_json()
    if not features:
        return jsonify({"error": "No features provided."}), 400

    # Ensure the features are in the correct order (same as during training)
    # You may want to store feature_names during training for robustness
    # For now, we assume the order is the same as in training_data[0]["features"].keys()
    with open("training_data.json", "r") as file:
        raw_data = json.load(file)
    training_data = raw_data.get("training_data", [])

    if not training_data:
        return jsonify({"error": "No valid training data available."}), 400
    feature_names = list(training_data[0]["features"].keys())
    X_input = [features['weather'].get(k, None) for k in feature_names]

    predictions = {}
    for label in [obj['image_category'] for obj in features['clothesCategories']]:
        try:
            clf = joblib.load(os.path.join(MODEL_DIR, f"{label}_rf.joblib"))
            le = joblib.load(os.path.join(MODEL_DIR, f"{label}_le.joblib"))
            pre = joblib.load(os.path.join(MODEL_DIR, f"{label}_pre.joblib"))

            X_trans = pre.transform([X_input])
            y_pred = clf.predict(X_trans)
            y_pred_label = le.inverse_transform(y_pred)
            predictions[label] = y_pred_label[0]
        except Exception as e:
            predictions[label] = f"Error: {str(e)}"

    return jsonify({"predictions": predictions}), 200


@app.route("/api/train_model", methods=['GET'])
def train_ml_model():
    
    # Load training data
    if not os.path.exists("training_data.json"):
        return jsonify({"error": "No training data found."}), 404

    with open("training_data.json", "r") as file:
        raw_data = json.load(file)

    # Flatten the data structure
    training_data = raw_data.get("training_data", [])


    if not training_data:
        return jsonify({"error": "No valid training data available."}), 400

    X_raw = [list(entry["features"].values()) for entry in training_data]

    # Identify categorical columns (assume str type is categorical)
    categorical_indices = [i for i, v in enumerate(X_raw[0]) if isinstance(v, str)]
    numeric_indices = [i for i, v in enumerate(X_raw[0]) if not isinstance(v, str)]

    # Prepare column transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_indices),
            ('num', 'passthrough', numeric_indices)
        ]
    )

    predictions = {}
    label_keys = set(training_data[0]["labels"].keys())
    
    for label_key in label_keys:
        y = [str(entry["labels"].get(label_key)) for entry in training_data]  # Convert None to "None" string


        # No need to filter out None labels now
        X_filtered = X_raw
        y_filtered = y

        # Encode labels if they are strings
        le = LabelEncoder()
        y_encoded = le.fit_transform(y_filtered)

        # Transform features
        X_transformed = preprocessor.fit_transform(X_filtered)

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_transformed, y_encoded)

        # Save model, label encoder, and preprocessor for this label
        joblib.dump(clf, os.path.join(MODEL_DIR, f"{label_key}_rf.joblib"))
        joblib.dump(le, os.path.join(MODEL_DIR, f"{label_key}_le.joblib"))
        joblib.dump(preprocessor, os.path.join(MODEL_DIR, f"{label_key}_pre.joblib"))

        # Predicting on the training set (for demonstration purposes)
        y_pred = clf.predict(X_transformed)

        # Decode predictions back to original labels
        y_pred_labels = le.inverse_transform(y_pred)
        predictions[label_key] = y_pred_labels.tolist()

    return jsonify({"predictions": predictions}), 200


if __name__ == '__main__':
    app.run(debug=True, host=os.getenv("computer_LAN_IP"), port=os.getenv("host_port"))  # Use environment variables for IP and port