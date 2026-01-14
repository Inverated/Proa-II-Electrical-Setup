#include <Adafruit_ADS1X15.h>
#include <SoftwareSerial.h>

//UART (Software) declaration
SoftwareSerial veSerial(D7, D8); // D4: RX, D5: TX will not be used 
//**Note: RX pin unable to receive signal across different boards**

// VE.Direct values
float V = 0;
float I = 0;
float VPV = 0;
int PPV = 0;
int CS = 0;
int MPPT = 0;
int ERR = 0;
String LOAD = "";

//ADS1115 for 5V Analog Sensor (HE Sensor)
Adafruit_ADS1115 ads;

// HE Sensor pins
int HESensorReading = 0;
int HESensorPin = 0;

//Timing values
unsigned long start_time;
unsigned long time_passed = 0;


void setup() {
  Serial.begin(74800);

  //Start SoftwareSerial UART
  veSerial.begin(19200);
  
  // Use voltage divider before connecting to ADS1115 
  //ads.setGain(GAIN_TWOTHIRDS);        // 2/3x gain   +/- 6.144V  1 bit = 0.1875mV
  //ads.setGain(GAIN_TWO);              // 1x gain   +/- 4.096V  1 bit = 0.125mV
  //Voltage output from 3V esp pin suddenly recorded at 4+V ???
  if (!ads.begin()) {
    Serial.println("Failed to initialize ADS.");
    while (1);
  }

  start_time = millis();
  Serial.println("Setup Complete Successfully\n");

  // Print header once
  Serial.println("Time(ms)\tV(V)\tI(A)\tVPV(V)\tPPV(W)\tCS\tMPPT\tERROR\tLOAD\tSensor Val");

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

void readCurrentSensor() {
  int16_t ADCReading = ads.readADC_SingleEnded(HESensorPin);
  float volts = ads.computeVolts(ADCReading);
  // Serial.print("AIN0: "); Serial.print(ADCReading); Serial.print("  "); Serial.print(volts); Serial.println("V");
  
  // Do calibration here with MPPT data
  HESensorReading = ADCReading;
}

void loop() {
  time_passed = millis() - start_time;

  bool validMPPT = parseMPPT();
  readCurrentSensor();

  if (validMPPT) {
    Serial.println("Hi");
    printRow();
  }
  delay(1000);
}

void printRow() {
  Serial.print(time_passed);     Serial.print('\t');
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
