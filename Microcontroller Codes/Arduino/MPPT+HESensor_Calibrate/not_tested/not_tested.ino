String key, value;

// VE.Direct values
float V = 0;
float I = 0;
float VPV = 0;
int PPV = 0;
int CS = 0;
int MPPT = 0;
int ERR = 0;
String LOAD = "";

// HE Sensor pins
int HESensorReading = 0;
int HESensorPin = A0;

//Timing values
unsigned long start_time;
unsigned long time_passed = 0;


void setup() {
  Serial.begin(19200);

  // Print header once
  Serial.println("Time(ms)\tV(V)\tI(A)\tVPV(V)\tPPV(W)\tCS\tMPPT\tLOAD\tSensor Val");

  start_time = millis();
}

bool parseMPPT() {
  if (!Serial1.available()) return false;

  String line = Serial1.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) return false;

  int tab = line.indexOf('\t');
  if (tab < 0) return false;

  key = line.substring(0, tab);
  value = line.substring(tab + 1);

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
  HESensorReading = analogRead(HESensorPin);
  // Do calibration here with MPPT data
}

void loop() {
  time_passed = millis() - start_time;

  bool validMPPT = parseMPPT();
  readCurrentSensor();

  if (validMPPT) {
    printRow();
  }
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
