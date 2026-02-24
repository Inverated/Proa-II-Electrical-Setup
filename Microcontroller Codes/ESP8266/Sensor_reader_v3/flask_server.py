from flask import Flask, jsonify, jsonify, request
import csv, os
from datetime import datetime

app = Flask(__name__)

CSV_FILE = "data_log.csv"

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["date", "time", "time_passed_since_start", "adc0_1", "adc1_1", "adc2_1", "adc3_1", "adc3_2", "Lost Data"])
        
@app.route('/sensordata', methods=['POST'])
def receive_data():
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
                entry.get("adc0_1"),
                entry.get("adc1_1"),
                entry.get("adc2_1"),
                entry.get("adc3_1"),
                entry.get("adc3_2"),
                entry.get("data_lost", 0)
            ])

    print(f"Saved {len(records)} records")
    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)