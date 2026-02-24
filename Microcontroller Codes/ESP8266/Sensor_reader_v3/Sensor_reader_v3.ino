#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads1;     
Adafruit_ADS1115 ads2;

void setup(void)
{
  Serial.begin(9600);

  Serial.println("ADC Range: +/- 6.144V (1 bit = 3mV/ADS1015, 0.1875mV/ADS1115)");

  if (!ads1.begin(0x48)) {
    Serial.println("Failed to initialize ADS 1.");
    while (1);
  }

  if (!ads2.begin(0x49)) {
    Serial.println("Failed to initialize ADS 2.");
    while (1);
  }
}

void loop(void)
{
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

  delay(1000);
}
