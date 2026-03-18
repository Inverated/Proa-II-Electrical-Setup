from collections import deque

from flask import Flask, jsonify, jsonify, request, render_template, Response
import csv
import os
import time
from datetime import datetime
from pathlib import Path
from ipBroadcast import discovery_server
import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from queue import Queue

app = Flask(__name__)

# hosts = ["192.168.50.63", "10.50.178.194"]
hosts = ["0.0.0.0"]
connected_devices = {}

CSV_FILE = Path(__file__).parent / \
    (datetime.now().date().isoformat() + "_data_log.csv")

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Time", "time_passed_since_start",
                         "ADS Reading 1", "Current 1",
                         "ADS Reading 2", "Current 2",
                         "ADS Reading 3", "Volts 1",
                         "Lost Data"])
    print(CSV_FILE, "created successfully")


# Graph
max_points = 500
voltage = deque(maxlen=max_points)
x_axis = deque(maxlen=max_points)
incoming = Queue()  # buffer between Flask and plot
counter = 0
fig, ax = plt.subplots()
ax.set_ylim(0, 60)
line, = ax.plot([], [])
counter = 0
last_t = None


def update(_):
    global counter
    global last_t
    updated = False

    # Pull all new data from Flask
    while not incoming.empty():
        t, v = incoming.get_nowait()
        if last_t is None or t >= last_t:
            last_t = t
            x_axis.append(t)
            voltage.append(v)
            updated = True

        if updated:
            line.set_data(list(x_axis), list(voltage))
            ax.relim()
            ax.autoscale_view(scaley=False)
    return line,


@app.before_request
def log_all_requests():
    if request.path == "/sensordata":
        print(f"Incoming request: {request.method} {request.path}")


def generate_messages():
    count = 0
    while True:
        time.sleep(2)  # simulate delay
        count += 1
        yield f"data: Message {count}\n\n"

# Utilising EventSource instead of Ajax for real-time updates
# Just one way communication to webpage only


@app.route('/stream')
def stream():
    return Response(generate_messages(), mimetype='text/event-stream')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sensordata', methods=['GET', 'POST'])
def receive_data():
    global counter

    print(f"Received {request.method} request at /sensordata")
    if request.method == 'GET':
        return jsonify({"message": "Send a POST request with sensor data in JSON format."}), 200

    data = request.get_json()

    if not data or "data" not in data:
        return jsonify({"error": "Invalid JSON"}), 400

    addr = data.get("address")
    if addr:
        mac_addr = addr.get("mac_address", "Unknown")
        if mac_addr not in connected_devices:
            connected_devices[mac_addr] = 1
        else:
            connected_devices[mac_addr] += 1

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
            incoming.put_nowait((counter, float(entry.get("volts_1", 0))))
            counter += 1

    print(f"Saved {len(records)} records")
    return jsonify({"status": "success"}), 200


def run_flask():
    connected = False
    for host in hosts:
        try:
            app.run(host=host, port=5000, debug=False)
            print(f"Server started on {host}")
            connected = True
            break
        except:
            print(f"Failed to start server on {host}\n")

    if not connected:
        app.run(host="0.0.0.0", port=5000, debug=False)
        print("Server started on default host")


if __name__ == '__main__':
    try:
        threading.Thread(target=discovery_server, daemon=True).start()
        threading.Thread(target=run_flask, daemon=True).start()

        ani = FuncAnimation(fig, update, interval=100, blit=False)
        plt.show()
    except:
        print("Shutting down server...")
        plt.close()
