#include <Adafruit_ADS1X15.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>

const char ssid[] = "Kor";
const char password[] = "idontknow";
const char* serverUrl = "http://192.168.50.63:5000/sensordata";

WiFiClient client;

unsigned long start_time;
unsigned long time_passed = 0;

Adafruit_ADS1115 ads1;     
Adafruit_ADS1115 ads2;

struct Sensor_Data {
  float time_passed;
  float adc0_1;
  float adc1_1;
  float adc2_1;
  float adc3_1;
  float adc3_2;
  int data_lost;
};

const int MAX_LENGTH = 10;
Sensor_Data cachedData[MAX_LENGTH];
int indexPos = 0;
int lostData = 0;

void setup(void)
{
  Serial.begin(9600);

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

  volts0_1 = ads1.computeVolts(adc0_1);
  volts1_1 = ads1.computeVolts(adc1_1);
  volts2_1 = ads1.computeVolts(adc2_1);
  volts3_1 = ads1.computeVolts(adc3_1);
  volts3_2 = ads2.computeVolts(adc3_2) * 12 * 1.05;

  Serial.println("-----------------------------------------------------------");
  Serial.print("AIN0_1: "); Serial.print(adc0_1); Serial.print("  "); Serial.print(volts0_1); Serial.println("V");
  Serial.print("AIN1_1: "); Serial.print(adc1_1); Serial.print("  "); Serial.print(volts1_1); Serial.println("V");
  Serial.print("AIN2_1: "); Serial.print(adc2_1); Serial.print("  "); Serial.print(volts2_1); Serial.println("V");
  Serial.print("AIN3_1: "); Serial.print(adc3_1); Serial.print("  "); Serial.print(volts3_1); Serial.println("V");
  Serial.print("AIN3_2: "); Serial.print(adc3_2); Serial.print("  "); Serial.print(volts3_2); Serial.println("V");

  cachedData[indexPos].time_passed = time_passed;
  cachedData[indexPos].adc0_1 = adc0_1;
  cachedData[indexPos].adc1_1 = adc1_1;
  cachedData[indexPos].adc2_1 = adc2_1;
  cachedData[indexPos].adc3_1 = adc3_1;
  cachedData[indexPos].adc3_2 = volts3_2;

  if (lostData > 0 || indexPos + 1 == MAX_LENGTH) {
    // Lost data continues to accumulate once the first data starts to be overridden
    // Stops counting once upload resumed
    lostData += 1;
    Serial.println("Data being overidden");
  }

  indexPos = (indexPos + 1) % MAX_LENGTH;

  if (indexPos > 0 && indexPos % 5 == 0) {
    uploadData() ? Serial.println("Data upload successful") : Serial.println("Data upload failed");
  }
  delay(1000);
}

bool uploadData() {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<1024> doc;
  JsonArray arr = doc.createNestedArray("data");

  for (int i = 0; i < indexPos; i++) {
    JsonObject obj = arr.createNestedObject();
    obj["time_passed"] = cachedData[i].time_passed;
    obj["adc0_1"] = cachedData[i].adc0_1;
    obj["adc1_1"] = cachedData[i].adc1_1;
    obj["adc2_1"] = cachedData[i].adc2_1;
    obj["adc3_1"] = cachedData[i].adc3_1;
    obj["adc3_2"] = cachedData[i].adc3_2;
    obj["data_lost"] = lostData + MAX_LENGTH;
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
