#include <ESP8266WiFi.h>
#include <espnow.h>
#include <map>

// Constants
const int SECONDS_IN_HOUR = 3600;
const int CALCULATION_INTERVAL = 1000; // ms

// Battery array details
const int SERIES = 2;
const int PARALLEL = 1;
const long PER_BATTERY_VOLTAGE = 25600;     //mV
const long PER_BATTERY_CAPACITY = 50000;    //mAh
const long INITIAL_CAPACITY = 50000;           //mAh (Use voltage-capacity to map later on. Ensure both is around same capacity/voltage initially)

unsigned long BATTERY_ARRAY_VOLTAGE = PER_BATTERY_VOLTAGE * SERIES;     // mV
unsigned long BATTERY_ARRAY_CAPACITY = PER_BATTERY_CAPACITY * PARALLEL * SECONDS_IN_HOUR;  // mAms
unsigned long current_level =  INITIAL_CAPACITY * PARALLEL * SECONDS_IN_HOUR;        // mAms
unsigned long prev_calculated_level = current_level;

typedef struct {
  int time_since_module_start;      // ms
  float mppt_current;   // mA
  float voltage;        // mV
  float HESensorOutput; // A
} MPPT_Sensor_Data;

MPPT_Sensor_Data data;

// Device Info
typedef struct {
  MPPT_Sensor_Data latest_data;
  unsigned long last_update_time;
  unsigned long last_calculated_time;
} ESP_Device_Info;

std::map<String, ESP_Device_Info> registeredDevices;

void setup() {
  Serial.begin(115200);
  Serial.print("MAC Address: ");
  Serial.println(WiFi.macAddress());
  
  Serial.println("\n=== Battery Configuration ===");
  Serial.print("Voltage: ");
  Serial.print(BATTERY_ARRAY_VOLTAGE / 1000.0, 1);
  Serial.println(" V");
  Serial.print("Capacity: ");
  Serial.print(BATTERY_ARRAY_CAPACITY / (1000.0 * SECONDS_IN_HOUR), 1);
  Serial.println(" Ah");
  Serial.print("Initial Level: ");
  Serial.print(current_level / (1000.0 * SECONDS_IN_HOUR), 1);
  Serial.println(" Ah");
  Serial.println("============================\n");

  WiFi.mode(WIFI_STA);
  if (esp_now_init() != 0) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  esp_now_set_self_role(ESP_NOW_ROLE_SLAVE);
  esp_now_register_recv_cb(onDataRecv);
}

void loop() {
  if (registeredDevices.size() <= 0) {
    delay(CALCULATION_INTERVAL);
    return;
  };

  for (auto& device : registeredDevices) {
    ESP_Device_Info& device_info = device.second;
    MPPT_Sensor_Data& device_data = device_info.latest_data;

    if (device_info.last_update_time > device_info.last_calculated_time) {
      unsigned long dt = device_info.last_update_time - device_info.last_calculated_time;
      noInterrupts();

      if (dt > 10000) {
        registeredDevices.erase(device.first);
      } else {
        current_level += dt * device_data.mppt_current;
        current_level -= dt * device_data.HESensorOutput * 1000;
        current_level = max(current_level, (unsigned long) 0);
        current_level = min(current_level, BATTERY_ARRAY_CAPACITY);
        device_info.last_calculated_time = device_info.last_update_time;
      }
      interrupts();      
    }
  }

  Serial.print("Current level (mAms): "); Serial.println(current_level);
  Serial.print("Total capacity (mAms): "); Serial.println(BATTERY_ARRAY_CAPACITY);
  Serial.print("SoC: "); Serial.print((current_level / (float) BATTERY_ARRAY_CAPACITY) * 100); Serial.println("%");

  float net_current_mA = current_level - prev_calculated_level;

  if (net_current_mA < -10.0) {  // Discharging
      float time_ms = current_level / abs(net_current_mA);
      Serial.print("Time to empty (s): ");
      Serial.println(time_ms / 1000.0);
  } else if (net_current_mA > 10.0) {  // Charging
      float time_ms = (BATTERY_ARRAY_CAPACITY - current_level) / net_current_mA;
      Serial.print("Time to full (s): ");
      Serial.println(time_ms / 1000.0);
  }
  prev_calculated_level = current_level;
  
  delay(CALCULATION_INTERVAL);
  yield();
}

void onDataRecv(uint8_t * mac, uint8_t *incomingData, uint8_t len) {
  memcpy(&data, incomingData, sizeof(data));

  char macChars[18];  //(2 addr + 1 terminator?) *6
  sprintf(macChars, "%02X:%02X:%02X:%02X:%02X:%02X",
              mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  
  String macAddr = String(macChars);
  ESP_Device_Info dev;

  dev.latest_data = data;
  dev.last_update_time = millis();
  dev.last_calculated_time = millis();

  if (registeredDevices.find(macAddr) != registeredDevices.end()) {
    // Do not reset the last calculated time
    dev.last_calculated_time = registeredDevices[macAddr].last_calculated_time;
  }

  Serial.println(dev.last_update_time);  
  registeredDevices[macAddr] = dev;

  Serial.print("\nReceived from: ");
  Serial.println(macAddr);
}