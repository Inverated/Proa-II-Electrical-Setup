from collections import deque
import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import serial  # pyserial
import serial.tools.list_ports
import struct
import csv
from pathlib import Path
import time

PACKET_BYTES = 4 + 2 + 4 + (8 * 2) + 2
FORMAT = '<H I 8H H' 

COUNT_BEFORE_FLUSH = 10000
PACKETS_PER_BULK = 10
SAMPLING_RATE = 20000
#BULK_READ_TIMEOUT = ((PACKET_BYTES * PACKETS_PER_BULK) / SAMPLING_RATE) + 0.1   # seconds — generous, ESP sends one bulk per 0.5s
BULK_READ_TIMEOUT = 1.5
TIME_BETWEEN_SAMPLES_ALERT = 5000 # 5ms
BULK_DATA_BYTES = PACKETS_PER_BULK * PACKET_BYTES

HEADER = b'\xEF\xBE\xAD\xDE'
HEADER_INT = 0xDEADBEEF

packets_cache = []

# Voltage (in raw adc values) plotter
MAX_POINTS = 5000
voltage = deque(maxlen=MAX_POINTS)
x_axis = deque(maxlen=MAX_POINTS)
fig, ax = plt.subplots()
ax.set_ylim(0, 54000)
line, = ax.plot([], [], lw=0.5)
last_time = 0


def update(frame):
    if len(x_axis) == 0:
        return line,
    ax.set_xlim(max(0, x_axis[-1] - MAX_POINTS), x_axis[-1] + 100)

    line.set_data(x_axis, voltage)
    return line,
    
date_now = time.strftime("%Y%m%d-%H%M%S")

print(f"Data will be saved to data_{date_now}.csv")
cwd = Path(__file__).parent
csv_file_path = Path(cwd) / f"data_{date_now}.csv"
exists = csv_file_path.exists()

csv_file = open(csv_file_path, mode='a', newline='')
writer = csv.writer(csv_file)
if not exists:
    writer.writerow(['counter', 'timediff_us', 'ch0', 'ch1', 'ch2',
                    'ch3', 'ch4', 'ch5', 'ch6', 'ch7'])
    csv_file.flush()

def read_exact(ser, n, timeout=BULK_READ_TIMEOUT):
    """Read exactly n bytes, blocking until all arrive or timeout."""
    data = bytearray()
    deadline = time.monotonic() + timeout
    while len(data) < n:
        if time.monotonic() > deadline:
            return None
        remaining = n - len(data)
        # returns up to `remaining`, waits up to ser.timeout
        chunk = ser.read(remaining)
        if chunk:
            data += chunk
    return bytes(data)

last_counter = -1
offset_counter = 0
broken_packet_count = 0

def read_bulk(ser):
    global packets_cache
    global broken_packet_count
    global last_counter, offset_counter
    
    if not sync_to_header(ser):
        print("Timed out waiting for bulk header.\t\t\t\t")
        return []

    # Header was consumed by sync_to_header, so only read the remaining bytes
    raw = read_exact(ser, BULK_DATA_BYTES - len(HEADER))
    if raw is None:
        print("Short read on bulk data.\t\t\t\t")
        return []

    raw = HEADER + raw  # Prepend the header back for packet parsing

    packets = []
    l_ptr = 0
    r_ptr = PACKET_BYTES
    while r_ptr <= len(raw):
        header_chunk = raw[l_ptr:l_ptr+4]
        header = struct.unpack('<I', header_chunk)[0]
        if header != HEADER_INT:
            ser.reset_input_buffer()
            # Re-alignment. Do not need to count towards broken
            l_ptr += 1
            r_ptr += 1
            continue
        
        body_chunk = raw[l_ptr+4:r_ptr]
        data = struct.unpack(FORMAT, body_chunk)
        counter, timediff = data[0], data[1]
        readings, chksum = data[2:10], data[10]


        if chksum != additive_cksum(readings, counter):
            print(f"Checksum fail, counter {counter}. Resyncing.\t\t\t\t")
            ser.reset_input_buffer()
            broken_packet_count += 1
            l_ptr += 1
            r_ptr += 1
            continue
        
        
        # Realign counter when there is a wraparround
        # Do not realign on broken packet, keep the jump
        if last_counter != -1:
            if counter < last_counter and (last_counter - counter) > 2**15: # Counter is 16 bit
                offset_counter = (last_counter + 1) - counter
            
        counter += offset_counter          
        last_counter = counter
                
        if timediff > TIME_BETWEEN_SAMPLES_ALERT:
            print(f"Large time gap detected: {timediff} us at counter {counter}\t\t\t\t")
            
        packets.append((counter, timediff, *readings))
        packets_cache.append((counter, timediff, *readings))
        l_ptr += PACKET_BYTES
        r_ptr += PACKET_BYTES

    packets_cache = []
    return packets


def sync_to_header(ser, timeout=BULK_READ_TIMEOUT):
    # Scan byte-by-byte until we find the 4-byte header.
    # Slightly inefficient but easier to implement
    
    buf = bytearray()
    deadline = time.monotonic() + timeout
    while True:
        if time.monotonic() > deadline:
            return False
        b = ser.read(1)
        if not b:
            continue
        buf += b
        if buf[-4:] == HEADER:
            return True


def additive_cksum(data, counter):
    sum = 0
    for index, value in enumerate(data):
        sum += value * (index + 1)
    return (sum + (counter & 0xFFFF)) % 65536

def begin_serial():
    global packets_cache
    global csv_file
    
    broken_packet_count = 0
    total_reconnection = 0
    total_reconnect_time = 0.0
    total_packets = 0
    time_start = time.monotonic()
    
    while True:
        try:
            ports = serial.tools.list_ports.comports()
            print(f"Found {len(ports)} serial ports.")

            if (len(ports) == 0):
                print("No serial ports found. Retrying...")
                time.sleep(1)
                continue

            for port in ports:
                try:
                    print(f"Trying {port.device}...")
                    if 'serial_device' in locals():
                        print("Closing previous serial connection...")
                        serial_device.close()
                        del serial_device
                        time.sleep(1)
                    serial_device = serial.Serial(port.device, 2000000, timeout=1)

                except serial.SerialException as e:
                    print(f"Failed to open {port.device}: {e}")
                    time.sleep(1)
                    continue

                found = False

                for _ in range(50):
                    serial_device.write(b"START\n")
                    serial_device.flush()
                    try:
                        line = serial_device.readline().decode('utf-8').strip()
                    except:
                        print("Ready flag not found. Checking for valid packet...")
                        if len(serial_device.readline()) == PACKET_BYTES:
                            found = True
                            break
                        continue
                    if "ADC Ready" in line:
                        found = True
                        break

                if not found:
                    print(f"Failed to connect to {port.device}. Closing port.")
                    serial_device.close()
                    continue

                print(f"Connected to {port.device}")
                reading_chunk = 1
                buffered_alert_counter = 0
                missing_packets = 0
                while True:
                    packet_list = read_bulk(serial_device)

                    if packet_list is None or len(packet_list) == 0:
                        print("No valid packets in bulk read.")
                        missing_packets += 1
                        if missing_packets == 1:
                            print("No packet received. Reconnecting...")
                            raise serial.SerialException("No packet received.")
                        time.sleep(0.1)
                        continue
                    missing_packets = 0

                    # Stagger alert notification
                    
                    reading_chunk += len(packet_list)
                    total_packets += len(packet_list)
                    if PACKETS_PER_BULK >= 1000 and SAMPLING_RATE <= 20000:
                        print(f"Received bulk of {len(packet_list)} packets. Counter range: {packet_list[0][0]} - {packet_list[-1][0]}")
                    
                    # Plot voltage over current time using just the last value from each bulk
                    voltage.append(packet_list[-1][8]) # ch6
                    x_axis.append(packet_list[-1][0]) # counter              
                    #print(f"Voltage: {packet_list[-1][8]} at counter {packet_list[-1][0]}\t\t\t\t")      
                    
                    waiting = serial_device.in_waiting
                    if waiting > BULK_DATA_BYTES:
                        buffered_alert_counter += 1
                        if buffered_alert_counter % 5000 == 0:
                            print(
                                f"Bytes waiting in buffer: {waiting}  ({waiting // PACKET_BYTES} packets behind)")
                    else:
                        buffered_alert_counter = 0

                    writer.writerows(packet_list)

                    if reading_chunk >= COUNT_BEFORE_FLUSH:
                        csv_file.flush()
                        print(
                            f"Saved {reading_chunk} packets. Total packets saved: {total_packets}", end="\r")
                        reading_chunk = 0
                    packet_list = []

        except KeyboardInterrupt:
            print("Exiting...")
            if "reading_chunk" in locals():
                print(f"Flushing remaining {reading_chunk} packets before exit.")
            csv_file.flush()
            csv_file.close()
            break
        except (csv.Error, ValueError) as e:
            csv_file = open(csv_file_path, mode='a', newline='')
            print(f"CSV error: {e}. Reopening CSV file.")
        except serial.serialutil.SerialException as e:
            reconnect_start_time = time.monotonic()
            total_reconnection += 1
            print(f"Serial exception: {e}. Attempting to reconnect...")
            try:
                print(
                    f"Remaining bytes in buffer before closing: {serial_device.in_waiting}")
                #serial_device.read(serial_device.in_waiting)
                #serial_device.flush()
                #serial_device.reset_input_buffer()
                #serial_device.reset_output_buffer()
                #serial_device.cancel_read()
                #serial_device.close()
                reconnect_time = time.monotonic() - reconnect_start_time
                print(f"Reconnection took {reconnect_time:.2f} seconds.")
                total_reconnect_time += reconnect_time
            except:
                print("Serial device already closed.")
            time.sleep(0.5)
        finally:
            print("\n--- Session Summary ---")
            time_end = time.monotonic()
            print(f"Session duration: {time_end - time_start:.2f} seconds")
            print(f"Total broken packets encountered: {broken_packet_count}")
            print(f"Total reconnections: {total_reconnection}")
            print(f"Total packets received: {total_packets}")
            print(
                f"Average packets per second: {total_packets / (time_end - time_start):.2f}")
            print(f"Net throughput: {((total_packets * PACKET_BYTES) / (time_end - time_start)) / 1024:.2f} KB/s")
            print(f"Total time spent reconnecting: {total_reconnect_time:.2f} seconds")
            
            try:
                print(
                    f"Flushing remaining {len(packets_cache)} packets to CSV before exit.")
                writer.writerows(packets_cache)
                csv_file.flush()
                print(
                    f"Final total packets saved: {total_packets + len(packets_cache)}\n")
            except:
                None
            if 'serial_device' in locals():
                try:
                    print(
                        f"Remaining bytes in buffer before closing: {serial_device.in_waiting}")
                    serial_device.read(serial_device.in_waiting)
                    #serial_device.flush()
                    #serial_device.reset_input_buffer()
                    #serial_device.reset_output_buffer()
                    #serial_device.cancel_read()
                    #serial_device.close()
                except:
                    print("Serial device already closed.")
            print("--- End of Session ---\n")
            # Do not close the CSV file here, as we want to keep it open for appending in the next loop iteration

if __name__ == "__main__":
    try:
        begin_serial()
        #threading.Thread(target=begin_serial, daemon=True).start()
        """ anim = FuncAnimation(fig, update, interval=100)
        plt.xlabel('Counter')
        plt.ylabel('Voltage (raw ADC)')
        plt.title('Real-time Voltage Plot')
        plt.show()
        """
        
    except Exception as e:
        print(f"Error in main thread: {e}")
        print("Exiting main thread.")
        plt.close()