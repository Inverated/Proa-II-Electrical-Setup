#include <LiquidCrystal_PCF8574.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <espnow.h>

#define LedSignalPin 2
bool ledState = false; 

//must match sender struct
typedef struct struct_message {
  int time_since_started;
  int dummy;
} SensorData;
SensorData message;

LiquidCrystal_PCF8574 lcd(0x27);

long sinceLastMessage = 0;

// Callback function that will be executed when data is received
void onDataRecv(uint8_t * mac, uint8_t *incomingData, uint8_t len) {
  memcpy(&message, incomingData, sizeof(message));

  char macChars[18];  //(2 addr + 1 terminator?) *6
  sprintf(macChars, "%02X:%02X:%02X:%02X:%02X:%02X",
              mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  
  String macAddr = String(macChars);
  Serial.print("\nReceived from: ");
  Serial.println(macAddr);
  
  Serial.print("Time passed: ");
  Serial.println(message.time_since_started);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Time passed:");
  lcd.setCursor(0, 1);
  lcd.print(message.time_since_started);

  // Blink when receiving
  ledSignal(1);
  sinceLastMessage = millis();
}

 
void setup() {
  Serial.begin(74880);
  pinMode(LedSignalPin, OUTPUT);
  Serial.print("ESP Board MAC Address:  ");
  Serial.println(WiFi.macAddress());
  
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);

  // Init ESP-NOW
  if (esp_now_init() != 0) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  
  //controller sends data, slave receive data
  esp_now_set_self_role(ESP_NOW_ROLE_SLAVE);
  esp_now_register_recv_cb(onDataRecv);

  Wire.begin(4, 5);   // SDA = GPIO4, SCL = GPIO5, D1
  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.setCursor(0, 0);
  lcd.print("Initialising");
}

void loop() {
  long timeSinceLastMessage = millis() - sinceLastMessage;
  
  if (timeSinceLastMessage > 1000) {
    ledSignal(-1);
  }
  delay(200);
}

void ledSignal(int state) { //what led do every second
  if (state == -1) {
    ledState = false;
    digitalWrite(LedSignalPin, ledState);
  } else if (state == 0) { //esp now not connected
      Serial.println("ESP-now failed to start");
      ledState = false;
      for (int i=0; i<10; i++) {
        digitalWrite(LedSignalPin, ledState);
        ledState = !ledState;
        delay(200);
      }
      
  } else if (state == 1) { //message delivered, blink once
    Serial.println("Message delivered successfully");    
    digitalWrite(LedSignalPin, ledState);
    ledState = !ledState;

  } else if (state == 2) { //message failed to deliver, blink twice
    Serial.println("Message failed to deliver");
    ledState = false;
    for (int i=0; i<4; i++) {
      digitalWrite(LedSignalPin, ledState);
      ledState = !ledState;
      delay(200);
      }
  }
}
