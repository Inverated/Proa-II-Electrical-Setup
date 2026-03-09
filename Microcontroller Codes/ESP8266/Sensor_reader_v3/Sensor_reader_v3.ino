#include <Adafruit_ADS1X15.h>
#include <ESP8266HTTPClient.h>

#include <ESP8266WiFi.h>
#include <ArduinoJson.h>

const char* ssids[] = {
  "POCO F6 Pro",
  "Kor"
};

const char* passwords[] = {
  "FeckingP@ssword84267256",
  "idontknow"
};

const char* localServerUrls[] = {
  "http://192.168.50.63:5000/sensordata",
  "http://10.50.178.194:5000/sensordata"
};
int foundServerIndex = -1;

WiFiClient client;
bool wifiIsConnected = false;

unsigned long start_time;
unsigned long time_passed = 0;

Adafruit_ADS1115 ads;     

// Output data
struct Sensor_Data {
  float time_passed;
  float ads_1;
  double current_1;
  float ads_2;
  double current_2;
  float ads_3;
  double volts_1;
  int data_lost;
};

// Data Transmission
const uint8_t MAX_LENGTH = 70;
Sensor_Data cachedData[MAX_LENGTH];
const uint8_t SEND_INTERVAL = 5;  
//send the data array after every interval of data read
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
const float ERROR_CORRECTION = 1.00;  //multiply by a factor

void setup(void) {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);

  Serial.println("Connecting to ADS1115");
  if (!ads.begin(0x48)) {
    Serial.println("Failed to initialize ADS.");
    while (1);
  }
  Serial.println("Connected to ASDS1115");

  connectToWifi();

  start_time = millis();
  Serial.println("Setup Complete Successfully\n");
}

void connectToWifi() {
  WiFi.mode(WIFI_STA);

  while (!wifiIsConnected) {
    for (int i = 0; i < sizeof(ssids) / sizeof(ssids[0]); i++) {
      if (wifiIsConnected) {
        break;
      }
      
      WiFi.begin(ssids[i], passwords[i]);
      Serial.print("Connecting to "); Serial.println(ssids[i]);

      for (int j = 0; j < 10; j++) {
        if (WiFi.status() != WL_CONNECTED) {
          Serial.print("Failed to connect. WiFi status: "); Serial.println(WiFi.status());
          delay(1000);
        } else {
          Serial.println("Connected to "); Serial.println(ssids[i]);
          wifiIsConnected = true;
          break;
        }
      }
    }
  }
}


void loop(void) {
  time_passed = millis() - start_time;

  int16_t adc1, adc2, adc3;
  float current_1, current_2, volts_1;

  // ADS integer reading
  adc1 = ads.readADC_SingleEnded(0);
  adc2 = ads.readADC_SingleEnded(1);
  adc3 = ads.readADC_SingleEnded(2);
  //ads reading at 5v = 80000/3 = 26667

  // Convert to current
  current_1 = adc1 / (80000 / 3.0) * 100;
  current_2 = adc2 / (80000 / 3.0) * 100;    
  volts_1 = ads.computeVolts(adc3) * SCALING * ERROR_CORRECTION;

  Serial.println("-----------------------------------------------------------");
  Serial.print("AIN0_1: "); Serial.print(adc1); Serial.print("  "); Serial.print(current_1); Serial.println("A");
  Serial.print("AIN1_1: "); Serial.print(adc2); Serial.print("  "); Serial.print(current_2); Serial.println("A");
  Serial.print("AIN2_1: "); Serial.print(adc3); Serial.print("  "); Serial.print(volts_1); Serial.println("V");

  cachedData[indexPos].time_passed = time_passed;
  cachedData[indexPos].ads_1 = adc1;
  cachedData[indexPos].ads_2 = adc2;
  cachedData[indexPos].ads_3 = adc3;
  cachedData[indexPos].current_1 = current_1;
  cachedData[indexPos].current_2 = current_2;
  cachedData[indexPos].volts_1 = volts_1;

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

  delay(500);
}

bool uploadData() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWifi();
  }

  StaticJsonDocument<1024> doc;
  JsonArray arr = doc.createNestedArray("data");

  JsonObject address = doc.createNestedObject("address");
  address["mac_address"] = WiFi.macAddress();

  for (int i = 0; i < indexPos; i++) {
    JsonObject obj = arr.createNestedObject();
    obj["time_passed"] = cachedData[i].time_passed;

    obj["ads_1"] = cachedData[i].ads_1;
    obj["ads_2"] = cachedData[i].ads_2;
    obj["ads_3"] = cachedData[i].ads_3;

    obj["current_1"] = cachedData[i].current_1;
    obj["current_2"] = cachedData[i].current_2;
    obj["volts_1"] = cachedData[i].volts_1;
    
    obj["data_lost"] = lostData > 0 ? lostData + MAX_LENGTH : 0;
  }

  String jsonString;
  serializeJson(doc, jsonString);

  HTTPClient http1;

  if (foundServerIndex == -1) {
    int arrSize = sizeof(localServerUrls) / sizeof(localServerUrls[0]);
    for (int i = 0; i < arrSize; i++) {
      http1.begin(client, localServerUrls[i]);
      http1.addHeader("Content-Type", "application/json");
      int response = http1.POST(jsonString);

      Serial.print("Local server ("); Serial.print(localServerUrls[i]); Serial.println(") response: ");
      Serial.println(response);

      http1.end();

      if (response == 200) {
        foundServerIndex = i;
        indexPos = 0;
        lostData = 0;
        return true;
      }
    }
  } else {
    http1.begin(client, localServerUrls[foundServerIndex]);
    http1.addHeader("Content-Type", "application/json");
    int response = http1.POST(jsonString);

    Serial.print("Local server response: ");
    Serial.println(response);

    http1.end();
    if (response == 200) {
      indexPos = 0;
      lostData = 0;
      return true;
    }
  }
  return false;
}
