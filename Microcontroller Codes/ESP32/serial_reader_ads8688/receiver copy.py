import serial  # pyserial
import serial.tools.list_ports
import struct
import csv
from pathlib import Path
import time

PACKET_SIZE = 2 + 4 + 4 + (8 * 2) + 2  # header + counter + time + readings + chksum in bytes
COUNT_BEFORE_FLUSH = 10000
ESP_SET_BUFFER_SIZE = 4000
MAX_BUFFER_BYTES = ESP_SET_BUFFER_SIZE * PACKET_SIZE
  
# 1k rows per second is stable
# 10k rows per second fails more frequently, prob due to not clearing serial buffer fast enough
# need to process asynchronously

cwd = Path(__file__).parent
csv_file_path = Path(cwd) / "data.csv"
exists = csv_file_path.exists()

csv_file = open(csv_file_path, mode='a', newline='')
writer = csv.writer(csv_file)
if not exists:
    writer.writerow(['counter', 'timediff_us', 'ch0', 'ch1', 'ch2',
            'ch3', 'ch4', 'ch5', 'ch6', 'ch7'])
    csv_file.flush()

HEADER1 = 0xAC
HEADER2 = 0xDC

HEADER = (HEADER2 << 8) | HEADER1  # Little-endian header value

broken_packet_count = 0
total_reconnection = 0
total_packets = 0

def read_packet(ser, remaining_bytes=None):   
    global broken_packet_count
    retries = 0
    while True:
        if ser.in_waiting == 0:
            if retries > 10:    # The ESP might take a while to fill up before sending in bulk
                serial_device.write(b"START\n")
                serial_device.flush()
                time.sleep(0.1)
                return None, None
            retries += 1
            continue
        else:
            break
    buffer = remaining_bytes + ser.read(ser.in_waiting) if remaining_bytes else ser.read(ser.in_waiting)
    packet_list = []
    
    has_broken_packet = False
    last_valid_counter = -1
    serial_overflow_counter = 0
    
    while len(buffer) >= PACKET_SIZE:
        if ser.in_waiting > MAX_BUFFER_BYTES:
            if serial_overflow_counter % 1000 == 0:
                print(f"Warning: Serial buffer has {ser.in_waiting} bytes waiting.")
            serial_overflow_counter += 1
        else:
            serial_overflow_counter = 0
        idx = buffer.find(b'\xDC\xAC')

        if idx < 0:
            print("Clearing")
            buffer = buffer[-1:]  # Keep the last byte in case it's the start of the header for the next packet
            break

        if len(buffer) < idx + PACKET_SIZE:
            break

        packet = buffer[idx:idx+PACKET_SIZE]
            
        res = process_packet_bytes(packet[2:])  # Exclude header bytes for processing
        
        if res[1] is None:
            # If packet is invalid, skip it and continue searching for the next header
            has_broken_packet = True
            print(f"Packet bytes: {buffer[:idx+PACKET_SIZE*2].hex()} is invalid. Skipping to next header.")
            buffer = buffer[idx+2:]
            print(f"Buffer after skipping: {buffer[:PACKET_SIZE*2].hex()}")
            continue
        
        if has_broken_packet and last_valid_counter != -1:  # Silenty pad missing rows
            counter = res[0]
            COUNTER_DIFF_THRESHOLD = 1000
            if counter > last_valid_counter:
                pass
            elif counter < last_valid_counter: # Counter reset and wraps around to 0
                wrap_around_diff = (0xFFFFFFFF - last_valid_counter) + counter + 1
                if wrap_around_diff < COUNTER_DIFF_THRESHOLD:
                    pass
                else:
                    print(f"Counter jump from {last_valid_counter} to {counter} is too large. Can't recover.")
            else:
                print(f"Counter jump from {last_valid_counter} to {counter} is too large. Can't recover.")
            total_broken = counter - last_valid_counter - 1 if counter > last_valid_counter else (counter + (0xFFFFFFFF - last_valid_counter) + 1) - 1
            broken_packet_count += total_broken
            print(f"Recovered {total_broken} missing packets between counters {last_valid_counter} and {counter}. Total broken packets so far: {broken_packet_count}")


        has_broken_packet = False
        last_valid_counter = res[0]
        packet_list.append(res)
        buffer = buffer[idx+PACKET_SIZE:]   
    
    return packet_list, buffer

def process_packet_bytes(packet_bytes):
    global total_packets
    if len(packet_bytes) != PACKET_SIZE - 2:
        raise ValueError(f"Invalid packet size: expected {PACKET_SIZE - 2} bytes, got {len(packet_bytes)} bytes.")    
    try:
        data = struct.unpack('<II8HH', packet_bytes)
        # Returns a tuple with the data split into the specified size
    except struct.error as e:
        print(f"Error unpacking packet: {e}")
        return (counter, None)
    
    counter = data[0]
    timediff_us = data[1]
    readings = data[2:10]
    chksum = data[10]
    
    additive_chksum = additive_cksum(readings, counter)
    if chksum != additive_chksum:
        print(f"Checksum mismatch at counter {counter}. "
            f"Calculated: {additive_chksum}, Received: {chksum}. "
            f"Diff: {abs(additive_chksum - chksum)}. "
            f"Packet bytes: {packet_bytes.hex()}")
        return (counter, None)
    return (counter, timediff_us, *readings)


def additive_cksum(data, counter):
    sum = 0
    for index, value in enumerate(data):
        sum += value * (index + 1)
    return (sum + (counter & 0xFFFF)) % 65536

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
            
            serial_device.reset_input_buffer()
            serial_device.reset_output_buffer()
            found = False

            for _ in range(50):
                serial_device.write(b"START\n")
                serial_device.flush()
                try:
                    line = serial_device.readline().decode('utf-8').strip()
                except:
                    print("Ready flag not found. Checking for valid packet...")
                    if len(serial_device.readline()) == PACKET_SIZE:
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
            has_broken_packet = False
            last_valid_counter = -1
            buffered_alert_counter = 0
            missing_packets = 0
            
            remaining_bytes = None
            while True:
                packet_list, remaining_bytes = read_packet(serial_device, remaining_bytes)
                
                if packet_list is None or len(packet_list) == 0:
                    missing_packets += 1
                    if missing_packets >= 50:
                        print("No packet received. Reconnecting...")
                        raise serial.SerialException("No packet received.")
                    time.sleep(0.1)
                    continue
                missing_packets = 0
                
                # Stagger alert notification                
                waiting = serial_device.in_waiting
                if waiting > MAX_BUFFER_BYTES:
                    buffered_alert_counter += 1
                    if buffered_alert_counter % 5000 == 0:
                        print(f"Bytes waiting in buffer: {waiting}  ({waiting // PACKET_SIZE} packets behind)")
                else:
                    buffered_alert_counter = 0
                
                writer.writerows(packet_list)
                reading_chunk += len(packet_list)
                total_packets += len(packet_list)
                
                if reading_chunk > COUNT_BEFORE_FLUSH:
                    csv_file.flush()
                    print(f"Saved {reading_chunk} packets. Total packets saved: {total_packets}", end="\r")
                    reading_chunk = 0
                packet_list = []
                
    except KeyboardInterrupt:
        print("Exiting...")
        print(f"Flushing remaining {reading_chunk} packets before exit.")
        csv_file.flush()
        csv_file.close()
        break
    except (csv.Error, ValueError) as e:
        csv_file = open(csv_file_path, mode='a', newline='')
        print(f"CSV error: {e}. Reopening CSV file.")
    except serial.serialutil.SerialException as e:
        total_reconnection += 1
        print(f"Serial exception: {e}. Attempting to reconnect...")
        serial_device.close()
        time.sleep(1)
    finally:
        print("\n--- Session Summary ---")
        print(f"Total broken packets encountered: {broken_packet_count}")
        print(f"Total reconnections: {total_reconnection}")
        print(f"Total packets received: {total_packets}")
        try:
            csv_file.flush()
        except:
            None
        if 'serial_device' in locals():
            try:
                print(f"Remainding bytes in buffer before closing: {serial_device.in_waiting}")
                serial_device.read(serial_device.in_waiting)
                serial_device.flush()
                serial_device.reset_input_buffer()
                serial_device.reset_output_buffer()
                serial_device.dtr = False
                serial_device.rts = False
                time.sleep(0.1)

                serial_device.close()
                serial_device.close()
            except:
                print("Serial device already closed.")
        print("--- End of Session ---\n")
        # Do not close the CSV file here, as we want to keep it open for appending in the next loop iteration