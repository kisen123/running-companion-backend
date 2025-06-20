from flask import Flask, request, jsonify, url_for

import os
import json
from dotenv import load_dotenv

load_dotenv()

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

    data = []

    for i, image_category in enumerate(image_categories):
        data.append({
            "category_id": str(i + 1),
            "image_category": image_category
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

    print(jsonify(data).data)
    return jsonify(data), 200



@app.route("/api/training_data", methods=['POST'])
def update_training_data():
    message = ""
    data = request.get_json()

    # Checking if a training data file exists. If not, we create one
    training_data_exists = os.path.exists("training_data.json")
    if not training_data_exists:
        with open("training_data.json", "w") as file:
            json.dump({}, file)
            message += "Training data file created, as it did not previously exist.\t"

    # Loading the existing training data
    with open("training_data.json", "r") as file:
        training_data = json.load(file)


    # Updating the training data with the new data
    if "training_data" in data:
        try:
            training_data.append(data["training_data"])
            message += "Training data updated successfully.\t"

            # Saving the updated training data back to the file
            with open("training_data.json", "w") as file:
                json.dump(training_data, file, indent=4)

        except KeyError:
            return jsonify({"error": "Invalid data format. 'training_data' key is required."}), 400
    
    
    # Here you would typically process the training data
    return jsonify({"message": "Training data received", "data": data}), 200






if __name__ == '__main__':
    app.run(debug=True, host=os.getenv("computer_LAN_IP"), port=os.getenv("host_port"))  # Use environment variables for IP and port