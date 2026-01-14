void setup() {
  Serial.begin(19200);
  Serial1.begin(19200);
  Serial.print("\nInit: ");
  Serial.println((uint8_t) "\n");

}

void loop() {
  if (Serial1.available()) {
    uint8_t b = Serial1.read();
    //Serial.print((char) b);

    //Serial.print("(");
    if (b == 10) {
      Serial.println("10");
    } else {
      Serial.print(b);
      Serial.print(" ");
    }
    
    //Serial.print(")");
  }
}