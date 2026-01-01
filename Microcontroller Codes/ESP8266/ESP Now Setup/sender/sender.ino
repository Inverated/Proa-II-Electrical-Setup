#include <ESP8266WiFi.h>
#include <espnow.h>

#define LedSignalPin 2
bool ledState = false;

typedef struct struct_message {
  int time_since_started;
} SensorData;
SensorData message;

bool espUp = false;

//address of receiving board
uint8_t broadcastAddress[] = {0x40, 0x91, 0x51, 0x4B, 0xB0, 0x8C};
bool messageSent;

unsigned long initialTime;


void ledSignal(int state) { //what led do every second
  if (state == 0) { //esp now not connected
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

void OnDataSent(uint8_t *mac_addr, uint8_t sendStatus) {
  if (sendStatus == 0){
    messageSent = true;
  }
  else{
    messageSent = false;
  }
}

void setup() {
  Serial.begin(74880);
  
  Serial.print("ESP Board MAC Address:  ");
  Serial.println(WiFi.macAddress());

  //set function of this pin to output
  pinMode(LedSignalPin, OUTPUT);  

  WiFi.mode(WIFI_STA);
  if (esp_now_init() != 0) {
    Serial.println("ESP-NOW init failed");
    return;
  }
  espUp = true;
  
  //controller sends data, slave receive data
  esp_now_set_self_role(ESP_NOW_ROLE_CONTROLLER);

  //run this fn on each sent
  esp_now_register_send_cb(OnDataSent);
  //send to this controller
  esp_now_add_peer(broadcastAddress, ESP_NOW_ROLE_SLAVE, 1, NULL, 0);
  
  initialTime = millis();
}

void loop() {
  if (!espUp) {
    ledSignal(0);
    delay(1000);
    return;
  };

  long time = (millis() - initialTime) / 1000;

	message.time_since_started = time;
  esp_now_send(broadcastAddress, (uint8_t*)&message, sizeof(message));

  if (messageSent) {
    ledSignal(1);
    Serial.print("Time since started: ");
    Serial.println(time);
  } else {
    ledSignal(2);
  }

  delay(1000);
}
