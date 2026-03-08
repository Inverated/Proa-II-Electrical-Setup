from flask import Flask, jsonify, jsonify, request
import csv, os
from datetime import datetime

app = Flask(__name__)

host = "192.168.50.63"
CSV_FILE = datetime.now().date().isoformat() + "_data_log.csv"

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Time", "time_passed_since_start", 
                         "ADS Reading 1", "Current 1", 
                         "ADS Reading 2", "Current 2",
                         "ADS Reading 3", "Volts 1",
                         "Lost Data"])

@app.before_request
def log_all_requests():
    print(f"Incoming request: {request.method} {request.path}")
    
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
                
                entry.get("ads_1"),
                entry.get("current_1"),
                
                entry.get("ads_2"),
                entry.get("current_2"),
                
                entry.get("ads_3"),
                entry.get("volts_1"),
                
                entry.get("data_lost", 0)
            ])

    print(f"Saved {len(records)} records")
    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(host=host, port=5000, debug=False)