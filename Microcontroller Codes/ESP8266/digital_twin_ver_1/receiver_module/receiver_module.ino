#include <ESP8266WiFi.h>
#include <espnow.h>
#include <map>

// Buffer
int FREQ = 1000; // ms

// Battery array details
int SERIES = 2;
int PARALLEL = 1;
float BATTERY_VOLTAGE = 25700 * SERIES;     // mV
float BATTERY_CAPACITY = 50000 * PARALLEL;  // mAh
float current_level = 50000 * PARALLEL;     // mAh (Ideally, use voltage - capacity to map initially)

typedef struct {
  int time_passed;      // ms
  float mppt_current;   // mA
  float voltage;        // mV
  float HESensorOutput; // A
} MPPT_Sensor_Data;

MPPT_Sensor_Data data;

// Input Count
int NUMBER_OF_ESP = 2;

// Device Info
typedef struct {
  MPPT_Sensor_Data latest_data;
  int time_passed; 
  int last_recorded_time;
} ESP_Device_Info;

std::map<String, ESP_Device_Info> registeredDevices;

unsigned long last_recorded_time = 0;

void setup() {
  Serial.begin(9600);
  Serial.print("ESP Board MAC Address:  ");
  Serial.println(WiFi.macAddress());

  WiFi.mode(WIFI_STA);
  if (esp_now_init() != 0) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  esp_now_set_self_role(ESP_NOW_ROLE_SLAVE);
  esp_now_register_recv_cb(onDataRecv);
}

void loop() {
  float total_mppt_out = 0;
  float total_load_in = 0;
  if (registeredDevices.size() >= NUMBER_OF_ESP) {
    for (const auto& device : registeredDevices) {
      ESP_Device_Info device_info = device.second;
      MPPT_Sensor_Data data = device_info.latest_data;
      if ((device_info.time_passed - device_info.last_recorded_time) > FREQ) {
        float time_passed_since_rec = device_info.time_passed - device_info.last_recorded_time;
        total_mppt_out += data.mppt_current * time_passed_since_rec;
        total_load_in += data.HESensorOutput * time_passed_since_rec;
        device_info.last_recorded_time = device_info.time_passed;
      }
    }
  }
  float calculated = total_mppt_out - total_load_in;
  current_level += min(calculated, BATTERY_CAPACITY);

  Serial.print(current_level);  
}

void onDataRecv(uint8_t * mac, uint8_t *incomingData, uint8_t len) {
  memcpy(&data, incomingData, sizeof(data));

  char macChars[18];  //(2 addr + 1 terminator?) *6
  sprintf(macChars, "%02X:%02X:%02X:%02X:%02X:%02X",
              mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  
  String macAddr = String(macChars);
  ESP_Device_Info dev;
  dev.latest_data = data;
  dev.time_passed = millis();
  dev.last_recorded_time = millis();

  if (registeredDevices.find(macAddr) != registeredDevices.end()) {
    // Do not reset the last recorded time
    dev.last_recorded_time = registeredDevices[macAddr].last_recorded_time;
  }

  Serial.println(dev.time_passed);  
  registeredDevices[macAddr] = dev;

  Serial.print("\nReceived from: ");
  Serial.println(macAddr);
}

void printData(MPPT_Sensor_Data data) {  
  Serial.print("Time Passed: ");
  Serial.println(data.time_passed);
  
  Serial.print("Current usage: ");
  Serial.println(data.HESensorOutput);
  
  Serial.print("MPPT Output Current: ");
  Serial.println(data.mppt_current);
  
  Serial.print("Circuit Voltage: ");
  Serial.println(data.voltage);
}