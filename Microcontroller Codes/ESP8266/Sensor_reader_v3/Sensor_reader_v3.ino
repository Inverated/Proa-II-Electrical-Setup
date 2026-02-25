#include <Adafruit_ADS1X15.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>

const char ssid[] = "POCO F6 Pro";
const char password[] = "FeckingP@ssword84267256";
const char* serverUrl = "http://10.175.182.194:5000/sensordata";
//const char* serverUrl = "https://verrucose-condensedly-ulises.ngrok-free.dev/sensordata";

WiFiClient client;

unsigned long start_time;
unsigned long time_passed = 0;

Adafruit_ADS1115 ads1;     
Adafruit_ADS1115 ads2;

// Output data
struct Sensor_Data {
  float time_passed;
  float volts0_1;
  float current_out_1;
  float volts1_1;
  float current_out_2;
  float volts2_1;
  float current_in_1;
  float volts3_1;
  float current_in_2;
  float volts3_2;
  int data_lost;
};

// Data Transmission
const uint8_t MAX_LENGTH = 100;
Sensor_Data cachedData[MAX_LENGTH];
const uint8_t SEND_INTERVAL = 5;
uint8_t indexPos = 0;
uint8_t lostData = 0;
bool uploadStatus = 0;

// WiFi status LED Pin
const uint8_t LED_PIN = 2;
uint8_t LED_status = 0;

// Voltage reader
const uint8_t V_READER_R1 = 110;   // kOhms
const uint8_t V_READER_R2 = 10;  // kOhms
const int SCALING = (V_READER_R2 + V_READER_R1) / V_READER_R2;
const float ERROR_CORRECTION = 1.015;  // 1%

void setup(void)
{
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);

  Serial.println("Connecting to ADS1115");
  if (!ads1.begin(0x48)) {
    Serial.println("Failed to initialize ADS 1.");
    while (1);
  }

  if (!ads2.begin(0x49)) {
    Serial.println("Failed to initialize ADS 2.");
    while (1);
  }
  Serial.println("Connected to both ASDS1115\n");

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.println(WiFi.status());
    delay(500);
  }
  Serial.println("Connected to WiFi");

  start_time = millis();
  Serial.println("Setup Complete Successfully\n");
}

void loop(void) {
  time_passed = millis() - start_time;
  
  int16_t adc0_1, adc1_1, adc2_1, adc3_1, adc3_2;
  float volts0_1, volts1_1, volts2_1, volts3_1, volts3_2;

  adc0_1 = ads1.readADC_SingleEnded(0);
  adc1_1 = ads1.readADC_SingleEnded(1);
  adc2_1 = ads1.readADC_SingleEnded(2);
  adc3_1 = ads1.readADC_SingleEnded(3);
  adc3_2 = ads2.readADC_SingleEnded(3);

  adc0_1 = adc0_1 < 600 ? 0 : adc0_1;
  adc1_1 = adc1_1 < 600 ? 0 : adc1_1;
  adc2_1 = adc2_1 < 600 ? 0 : adc2_1;
  adc3_1 = adc3_1 < 600 ? 0 : adc3_1;
  adc3_2 = adc3_2 < 600 ? 0 : adc3_2;

  volts0_1 = ads1.computeVolts(adc0_1);
  volts1_1 = ads1.computeVolts(adc1_1);
  volts2_1 = ads1.computeVolts(adc2_1);
  volts3_1 = ads1.computeVolts(adc3_1);
  volts3_2 = ads2.computeVolts(adc3_2) * SCALING * ERROR_CORRECTION;

  Serial.println("-----------------------------------------------------------");
  Serial.print("AIN0_1: "); Serial.print(adc0_1); Serial.print("  "); Serial.print(volts0_1); Serial.println("V");
  Serial.print("AIN1_1: "); Serial.print(adc1_1); Serial.print("  "); Serial.print(volts1_1); Serial.println("V");
  Serial.print("AIN2_1: "); Serial.print(adc2_1); Serial.print("  "); Serial.print(volts2_1); Serial.println("V");
  Serial.print("AIN3_1: "); Serial.print(adc3_1); Serial.print("  "); Serial.print(volts3_1); Serial.println("V");
  Serial.print("AIN3_2: "); Serial.print(adc3_2); Serial.print("  "); Serial.print(volts3_2); Serial.println("V");

  cachedData[indexPos].time_passed = time_passed;
  cachedData[indexPos].volts0_1 = volts0_1;
  cachedData[indexPos].volts1_1 = volts1_1;
  cachedData[indexPos].volts2_1 = volts2_1;
  cachedData[indexPos].volts3_1 = volts3_1;
  cachedData[indexPos].volts3_2 = volts3_2;

  if (lostData > 0 || indexPos + 1 == MAX_LENGTH) {
    // Lost data continues to accumulate once the first data starts to be overridden
    // Stops counting once upload resumed
    lostData += 1;
    Serial.println("Data being overidden");
  }

  indexPos = (indexPos + 1) % MAX_LENGTH;

  if (indexPos > 0 && indexPos % SEND_INTERVAL == 0) {
    if (uploadData()) {
      Serial.println("Data upload successful");
      uploadStatus = 1;
    } else {
      Serial.println("Data upload failed");
      uploadStatus = 0;
    }
  }

  if (!uploadStatus) {
    LED_status = !LED_status;
    digitalWrite(LED_PIN, LED_status);
  } else {
    LED_status = 1;
    digitalWrite(LED_PIN, LED_status);
  }

  delay(1000);
}

bool uploadData() {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("ngrok-skip-browser-warning", "true");

  StaticJsonDocument<1024> doc;
  JsonArray arr = doc.createNestedArray("data");

  for (int i = 0; i < indexPos; i++) {
    JsonObject obj = arr.createNestedObject();
    obj["time_passed"] = cachedData[i].time_passed;

    obj["volts0_1"] = cachedData[i].volts0_1;
    obj["current_out_1"] = 100 * cachedData[i].volts0_1 / 5.0;

    obj["volts1_1"] = cachedData[i].volts1_1;
    obj["current_out_2"] = 100 * cachedData[i].volts1_1 / 5.0;

    obj["volts2_1"] = cachedData[i].volts2_1;
    obj["current_in_1"] = 100 * cachedData[i].volts2_1 / 5.0;

    obj["volts3_1"] = cachedData[i].volts3_1;
    obj["current_in_2"] = 100 * cachedData[i].volts3_1 / 5.0;

    obj["volts3_2"] = cachedData[i].volts3_2;
    
    obj["data_lost"] = lostData > 0 ? lostData + MAX_LENGTH : 0;
  }

  String jsonString;
  serializeJson(doc, jsonString);

  int response = http.POST(jsonString);

  Serial.print("Server response: ");
  Serial.println(response);

  http.end();

  if (response == 200) {
    indexPos = 0;
    lostData = 0;
    return true;
  } else {
    return false;
  }
}
