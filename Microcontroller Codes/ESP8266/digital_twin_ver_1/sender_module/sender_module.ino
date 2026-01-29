#include <ESP8266WiFi.h>
#include <espnow.h>
#include <Adafruit_ADS1X15.h>
#include <SoftwareSerial.h>

#define LedSignalPin 2

//UART (Software) declaration
SoftwareSerial veSerial(D7, D8); // D4: RX, D5: TX will not be used 
//**Note: RX pin unable to receive signal across different boards**

bool ENABLE_SERIAL_LOGGING = true;
bool ENABLE_ESP_STATUS_LOGGING = false;
bool ENABLE_ANALOG_CURRENT_SIM = true;

// VE.Direct values
bool validMPPT = false;
int V = 0;
float I = 0;
float VPV = 0;
int PPV = 0;
int CS = 0;
int MPPT = 0;
int ERR = 0;
String LOAD = "OFF";

//ADS1115 for 5V Analog Sensor (HE Sensor)
Adafruit_ADS1115 ads;

// HE Sensor pins
const int HESensorPin = 0;
const int HESensorMaxI = 100000; //mA
int HESensorReading = 0;

// Pin for simulating current draw from MPPT
const int ISimOutPin = 1;
int ISimOutReading = 0;
float MPPTMaxIOut = 45000;  //mA
float CircuitVoltageReading = 26560;

//Timing values
unsigned long start_time;
unsigned long time_passed = 0;

// Setup ESP Now
uint8_t broadcastAddress[] = {0x40, 0x91, 0x51, 0x4A, 0xCD, 0x08};
bool messageSent;

typedef struct {
  unsigned long time_since_module_start;
  float mppt_current;
  float voltage;
  float HESensorOutput;
} MPPT_Sensor_Data;

MPPT_Sensor_Data data;

void setup() {
  Serial.begin(9600);
  pinMode(LedSignalPin, OUTPUT);

  // Use voltage divider before connecting to ADS1115 
  ads.setGain(GAIN_TWOTHIRDS);        // 2/3x gain   +/- 6.144V  1 bit = 0.1875mV
  //ads.setGain(GAIN_TWO);              // 1x gain   +/- 4.096V  1 bit = 0.125mV
  //Voltage output from 3V esp pin suddenly recorded at 4+V ???
  if (!ads.begin()) {
    if (ENABLE_ESP_STATUS_LOGGING) Serial.println("Failed to initialize ADS.");
    while (1);
  }

  if (!ENABLE_ANALOG_CURRENT_SIM) {
    //Start SoftwareSerial UART
    veSerial.begin(19200);
  }
  
  // Initialise esp now
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != 0) {
    if (ENABLE_SERIAL_LOGGING) Serial.println("ESP-NOW init failed");
    return;
  } else {
    if (ENABLE_SERIAL_LOGGING) Serial.println("ESP-NOW init successful");
  }

  // Controller sends data, slave receive data
  esp_now_set_self_role(ESP_NOW_ROLE_CONTROLLER);
  esp_now_register_send_cb(onSend);
  // Register to this controller
  esp_now_add_peer(broadcastAddress, ESP_NOW_ROLE_SLAVE, 0, NULL, 0);

  if (ENABLE_SERIAL_LOGGING) {
    Serial.println("Setup Complete Successfully\n");
    // Print header once
    Serial.println("Time(ms)\tV(mV)\tI(mA)\tVPV(V)\tPPV(W)\tCS\tMPPT\tERROR\tLOAD\tSensor (mA)");
  }

  start_time = millis();
}

void loop() {
  time_passed = millis() - start_time;

  if (ENABLE_ANALOG_CURRENT_SIM) {
    validMPPT = parseSimMPPT();
  } else {
    validMPPT = parseMPPT();
  }

  readCurrentSensor();
  if (validMPPT) {
    compileMessage();
    esp_now_send(broadcastAddress, (uint8_t*)&data, sizeof(data));
    if (ENABLE_SERIAL_LOGGING) printRow();
  }
  delay(1000);
}

void compileMessage() {
  data.time_since_module_start = time_passed;
  data.HESensorOutput = max(0, HESensorReading);
  data.mppt_current = I;
  data.voltage = V;
}

void onSend(uint8_t *mac_addr, uint8_t sendStatus) {
  if (ENABLE_ESP_STATUS_LOGGING) {
    Serial.print("Send status: ");
    Serial.println(sendStatus == 0 ? "Success" : "Fail");
  }
  digitalWrite(LedSignalPin, sendStatus);
}

void printRow() {
  Serial.print(time_passed);     Serial.print("\t\t");
  Serial.print(V);        Serial.print('\t');
  Serial.print(I);        Serial.print('\t');
  Serial.print(VPV);      Serial.print('\t');
  Serial.print(PPV);      Serial.print('\t');
  Serial.print(CS);       Serial.print('\t');
  Serial.print(MPPT);     Serial.print('\t');
  Serial.print(ERR);      Serial.print('\t');
  Serial.print(LOAD);     Serial.print('\t');
  Serial.println(HESensorReading);
}

void readCurrentSensor() {
  int16_t ADCReading = ads.readADC_SingleEnded(HESensorPin);
  float volts = ads.computeVolts(ADCReading);
  
  // Do calibration here with MPPT data
  // Untested: Please update after doing actual test
  float ratio = volts / 3.3;
  HESensorReading = ratio * HESensorMaxI; //Rated 100A he sensor
}

bool parseSimMPPT() {
  int16_t ADCReading = ads.readADC_SingleEnded(ISimOutPin);
  float volts = ads.computeVolts(ADCReading);

  float ratio = volts / 3.3;
  I = max((float) 0.0, ratio * MPPTMaxIOut);
  V = CircuitVoltageReading;
  LOAD = "ON";
  return true;
}

bool parseMPPT() {    // UART pin for esp8266 = Serial.read, not Serial1 
  if (!veSerial.available()) {
    return false;
  }

  String line = veSerial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) return false;

  int tab = line.indexOf('\t');
  if (tab < 0) return false;

  String key = line.substring(0, tab);
  String value = line.substring(tab + 1);

  if (key == "V") {
    V = value.toInt();
  } else if (key == "I") {
    I = value.toInt();
  } else if (key == "VPV") {
    VPV = value.toInt();
  } else if (key == "PPV") {
    PPV = value.toInt();
  } else if (key == "CS") {
    CS = value.toInt();
  } else if (key == "MPPT") {
    MPPT = value.toInt();
  } else if (key == "LOAD") {
    LOAD = value;
  } else if (key == "ERR") {
    ERR = value.toInt();
  }

  // End of frame
  if (key != "Checksum") {
    return false;
  }
  return true;
}