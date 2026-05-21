import serial  # pyserial
import serial.tools.list_ports
import struct
import csv
from pathlib import Path
import time

COUNT_BEFORE_FLUSH = 1000

cwd = Path(__file__).parent
csv_file_path = Path(cwd) / "data.csv"
exists = csv_file_path.exists()

csv_file = open(csv_file_path, mode='a', newline='')
writer = csv.writer(csv_file)
if not exists:
    writer.writerow(['counter', 'timestamp', 'timediff_us', 'ch0', 'ch1', 'ch2',
            'ch3', 'ch4', 'ch5', 'ch6', 'ch7', 'crc'])
    csv_file.flush()

HEADER = 0x1411
PACKET_SIZE = 2 + 4 + 4 + (8 * 2) + 2  # header + counter + time + readings + crc in bytes
def read_packet(ser):
    while True:
        b = ser.read(2)
        if b and struct.unpack('<H', b)[0] == HEADER:
            rest = ser.read(PACKET_SIZE - 2)
            if len(rest) != PACKET_SIZE - 2:
                return None
            return b + rest

def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

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
                serial_device = serial.Serial(port.device, 2000000, timeout=1)
                
            except serial.SerialException as e:
                print(f"Failed to open {port.device}: {e}")
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
            
            while True:
                packet = read_packet(serial_device)
                
                # Stagger alert notification                
                waiting = serial_device.in_waiting
                if waiting // PACKET_SIZE > 500:
                    buffered_alert_counter += 1
                    if buffered_alert_counter % 10 == 0:
                        print(f"Bytes waiting in buffer: {waiting}  ({waiting // PACKET_SIZE} packets behind)")
                else:
                    buffered_alert_counter = 0
                    
                if packet is None:
                    print("No packet received. Retrying...")
                    continue
                if len(packet) != PACKET_SIZE:
                    print(f"Expected {PACKET_SIZE} bytes, but got {len(packet)}. Skipping packet.")
                    print("Incomplete packet received. Skipping.")
                    has_broken_packet = True
                    continue

                """
                    struct __attribute__((packed)) Packet {
                        uint16_t header;
                        uint32_t counter;
                        uint32_t timediff_us;		// Use micros. Sampling 1 / ms, use us for precision; 32bit -> ~70 min
                        uint16_t readings[8];
                        uint16_t crc;
                    };
                """
                try:
                    data = struct.unpack('<HII8HH', packet)
                    # Returns a tuple with the data split into the specified size
                except struct.error as e:
                    print(f"Error unpacking packet: {e}")
                    has_broken_packet = True
                    continue
                
                header = data[0]
                if (header != HEADER):
                    print(f"Invalid header: {header}. Expected {HEADER}. Skipping packet.")
                    has_broken_packet = True
                    continue
                
                counter = data[1]
                timediff_us = data[2]
                readings = data[3:11]
                crc = data[11]
                now = time.time()
                
                raw_bytes = struct.pack('<HII8H', header, counter, timediff_us, *readings)
                calculated_crc = crc16(raw_bytes)
                if calculated_crc != crc:
                    print(f"CRC mismatch at counter {counter}. Calculated: {calculated_crc}, Received: {crc}. Skipping packet.")
                    has_broken_packet = True
                    continue
                
                COUNTER_DIFF_THRESHOLD = 1000
                if has_broken_packet and last_valid_counter != -1:
                    if counter > last_valid_counter:
                        timediff_us *= (counter - last_valid_counter)
                    elif counter < last_valid_counter: # Counter reset and wraps around to 0
                        wrap_around_diff = (0xFFFFFFFF - last_valid_counter) + counter + 1
                        if wrap_around_diff < COUNTER_DIFF_THRESHOLD:
                            timediff_us *= (counter + (0xFFFFFFFF - last_valid_counter) + 1)    
                    else:
                        print(f"Counter jump from {last_valid_counter} to {counter} is too large. Can't recover.")

                    has_broken_packet = False
                    
                last_valid_counter = counter
                writer.writerow([counter, timediff_us, *readings, crc])
                
                if reading_chunk >= COUNT_BEFORE_FLUSH:
                    csv_file.flush()
                    print(f"Saved {reading_chunk} packets.")
                    reading_chunk = 1
                else:                
                    reading_chunk += 1
                
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
        print("Serial port has been disconnected. Attempting to reconnect...")
        serial_device.close()
        time.sleep(3)
    finally:
        try:
            csv_file.flush()
        except:
            None
        if 'serial_device' in locals():
            serial_device.close()
            
        # Do not close the CSV file here, as we want to keep it open for appending in the next loop iteration