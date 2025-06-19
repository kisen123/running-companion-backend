from flask import Flask, request, jsonify

import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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



@app.route("/training_data", methods=['POST'])
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
    app.run(debug=True, host=os.getenv("computer_LAN_IP"), port=os.getenv("host_post"))  # Use environment variables for IP and port