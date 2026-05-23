import serial  # pyserial
import serial.tools.list_ports
import struct
import csv
from pathlib import Path
import time

PACKET_SIZE = 2 + 4 + 4 + (8 * 2) + 2  # header + counter + time + readings + crc in bytes
COUNT_BEFORE_FLUSH = 5000
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
    writer.writerow(['timestamp','counter', 'timediff_us', 'ch0', 'ch1', 'ch2',
            'ch3', 'ch4', 'ch5', 'ch6', 'ch7'])
    csv_file.flush()

HEADER1 = 0xAC
HEADER2 = 0xDC
HEADER = (HEADER2 << 8) | HEADER1  # Little-endian header value

broken_packet_count = 0
total_reconnection = 0
total_packets = 0

def read_packet(ser):
    retries = 0
    prev_byte = 0x00
    while True:
        try:
            if ser.in_waiting == 0:
                if retries > 50:    # The ESP might take a while to fill up before sending in bulk
                    #print(f"Checking for packet header... (Retry: {retries})")
                    #print(f"Bytes waiting in buffer: {ser.in_waiting}")
                    serial_device.write(b"START\n")
                    serial_device.flush()
                    time.sleep(0.1)
                    return None
                retries += 1
                continue
            
            # Consume all header byte before the actual packet
            next_byte = ser.read(1)
            if len(next_byte) == 0:
                retries += 1
                continue
            if next_byte[0] != HEADER1 and next_byte[0] != HEADER2:
                retries += 1
                prev_byte = next_byte[0]
                continue
            if next_byte[0] == HEADER2 and prev_byte != HEADER1:
                retries += 1
                prev_byte = next_byte[0]
                continue
            if next_byte[0] != HEADER1 and prev_byte != HEADER2:
                retries += 1
                prev_byte = next_byte[0]
                continue
            # Passes only if prev_byte is HEADER2 and next_byte is HEADER1

            rest = ser.read(PACKET_SIZE - 2)

            if len(rest) != PACKET_SIZE - 2:
                retries += 1
                prev_byte = rest[-1] if len(rest) > 0 else 0x00
                continue
            return rest
        
        except serial.SerialException as e:
            raise e

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
            time.sleep(3)
            continue

        for port in ports:
            try:
                print(f"Trying {port.device}...")
                if 'serial_device' in locals():
                    print("Closing previous serial connection...")
                    serial_device.close()
                    del serial_device
                    time.sleep(1)
                serial_device = serial.Serial(port.device, 1000000, timeout=1)
                
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
            
            
            while True:
                packet = read_packet(serial_device)
                if packet is None:
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
                if len(packet) != PACKET_SIZE - 2:
                    print(f"Expected {PACKET_SIZE - 2} bytes (Excluding header), but got {len(packet)}. Skipping packet.")
                    print("Incomplete packet received. Skipping.")
                    has_broken_packet = True
                    broken_packet_count += 1
                    continue
                
                try:
                    data = struct.unpack('<II8HH', packet)
                    # Returns a tuple with the data split into the specified size
                except struct.error as e:
                    print(f"Error unpacking packet: {e}")
                    has_broken_packet = True
                    broken_packet_count += 1
                    continue

                counter = data[0]
                timediff_us = data[1]
                readings = data[2:10]
                crc = data[10]
                now = time.time()
                    
                additive_crc = additive_cksum(readings, counter)
                if crc != additive_crc:
                    print(f"Checksum mismatch at counter {counter}. Calculated: {additive_crc}, Received: {crc}. Skipping packet.")
                    print(f"Saved {reading_chunk - reading_chunk % COUNT_BEFORE_FLUSH} packets.", end="\r")
                    has_broken_packet = True
                    broken_packet_count += 1
                    continue
                
                COUNTER_DIFF_THRESHOLD = 1000
                if has_broken_packet and last_valid_counter != -1:  # Silenty pad missing rows
                    if counter > last_valid_counter:
                        timediff_us *= (counter - last_valid_counter)
                    elif counter < last_valid_counter: # Counter reset and wraps around to 0
                        wrap_around_diff = (0xFFFFFFFF - last_valid_counter) + counter + 1
                        if wrap_around_diff < COUNTER_DIFF_THRESHOLD:
                            timediff_us *= (counter + (0xFFFFFFFF - last_valid_counter) + 1)
                    else:
                        print(f"Counter jump from {last_valid_counter} to {counter} is too large. Can't recover.")

                    has_broken_packet = False
                    #broken_packet_count += counter - last_valid_counter - 1 if counter > last_valid_counter else (counter + (0xFFFFFFFF - last_valid_counter) + 1) - 1

                last_valid_counter = counter
                writer.writerow([now, counter, timediff_us, *readings])
                if reading_chunk % COUNT_BEFORE_FLUSH == 0:
                    csv_file.flush()
                    print(f"Saved {reading_chunk} packets.", end="\r")
                reading_chunk += 1
                total_packets += 1
                
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
    except Exception as e:
        print(f"Unexpected error: {e}. Attempting to continue...")
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
                serial_device.flush()
                serial_device.reset_input_buffer()
                serial_device.reset_output_buffer()
                serial_device.close()
            except:
                print("Serial device already closed.")
        print("--- End of Session ---\n")
        # Do not close the CSV file here, as we want to keep it open for appending in the next loop iteration