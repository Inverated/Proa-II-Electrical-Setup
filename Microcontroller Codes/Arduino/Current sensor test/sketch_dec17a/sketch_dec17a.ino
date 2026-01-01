#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Common I2C address: 0x27 or 0x3F
LiquidCrystal_I2C lcd(0x27, 16, 2);
int HESensorPin = A0;

int ZERO_READING = 0;
float INTERVAL_PER_AMP = 25/5;

unsigned long start_time;
unsigned long last_update_time = 0;
const unsigned long LCD_UPDATE_INTERVAL = 500; // Update LCD every 500ms
const unsigned long READING_INTERVAL = 200;

void setup() {
  Serial.begin(9600);

  lcd.init();          // Initialize LCD
  lcd.backlight();     // Turn on backlight
  lcd.setCursor(0,0);
  lcd.print('Hi');

  start_time = millis();
}

int now = 0;

void loop() {
  int value = analogRead(HESensorPin);
  float current = (value - ZERO_READING) / INTERVAL_PER_AMP;

  unsigned long time_passed = (millis() - start_time) / 1000;

  if (millis() - last_update_time >= LCD_UPDATE_INTERVAL) {
    last_update_time = millis();
    
    // Clear LCD and display new values
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Time: ");
    lcd.print(time_passed);
    lcd.print("s");
    
    lcd.setCursor(0, 1);
    lcd.print("Current: ");
    lcd.print(current);
    lcd.print("A");
  }

  Serial.print("Time: ");
  Serial.print(millis() - start_time);
  Serial.print("ms\tReading: ");
  Serial.print(value);
  Serial.print("\tCurrent: ");
  Serial.println(current);
  delay(READING_INTERVAL);  
}
