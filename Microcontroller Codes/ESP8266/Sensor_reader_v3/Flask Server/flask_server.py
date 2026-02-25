from flask import Flask, jsonify, jsonify, request
import csv, os
from datetime import datetime

app = Flask(__name__)

CSV_FILE = "data_log.csv"

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["date", "time", "time_passed_since_start", 
                         "Volt Reading 1", "Current Out 1", 
                         "Volt Reading 2", "Current Out 2",
                         "Volt Reading 3", "Current In 1",
                         "Volt Reading 4", "Current In 2",
                         "Voltage", 
                         "Lost Data"])

@app.route("/", methods=['GET'])
def home():
    return "ESP8266 Sensor Data Receiver is running."   
    
@app.route('/sensordata', methods=['GET', 'POST'])
def receive_data():
    print(f"Received {request.method} request at /sensordata")
    if request.method == 'GET':
        return jsonify({"message": "Send a POST request with sensor data in JSON format."}), 200
        
    data = request.get_json()

    if not data or "data" not in data:
        return jsonify({"error": "Invalid JSON"}), 400

    records = data["data"]

    date_now = datetime.now().date().isoformat()
    time_now = datetime.now().time().isoformat()
    
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)

        for entry in records:
            writer.writerow([
                date_now,
                time_now,
                entry.get("time_passed"),
                
                entry.get("volts0_1"),
                entry.get("current_out_1"),
                
                entry.get("volts1_1"),
                entry.get("current_out_2"),
                
                entry.get("volts2_1"),
                entry.get("current_in_1"),
                
                entry.get("volts3_1"),
                entry.get("current_in_2"),
                
                entry.get("volts3_2"),
                
                entry.get("data_lost", 0)
            ])

    print(f"Saved {len(records)} records")
    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)