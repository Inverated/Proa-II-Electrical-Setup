#include <ESP8266WiFi.h>
#include <espnow.h>

typedef struct {
  int time_passed;
  float mppt_current;
  float voltage;
  float HESensorOutput;
} MPPT_Sensor_Data;

MPPT_Sensor_Data data;

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
  // put your main code here, to run repeatedly:

}

void onDataRecv(uint8_t * mac, uint8_t *incomingData, uint8_t len) {
  memcpy(&data, incomingData, sizeof(data));

  char macChars[18];  //(2 addr + 1 terminator?) *6
  sprintf(macChars, "%02X:%02X:%02X:%02X:%02X:%02X",
              mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  
  String macAddr = String(macChars);
  Serial.print("\nReceived from: ");
  Serial.println(macAddr);
  
  Serial.print("Time Passed: ");
  Serial.println(data.time_passed);
  
  Serial.print("Current usage: ");
  Serial.println(data.HESensorOutput);
  
  Serial.print("MPPT Output Current: ");
  Serial.println(data.mppt_current);
  
  Serial.print("Circuit Voltage: ");
  Serial.println(data.voltage);
}