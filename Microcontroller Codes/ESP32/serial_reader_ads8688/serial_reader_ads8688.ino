#include <ADS8688.h>
#include "esp_rom_crc.h"

#define PIN_CS 7
#define PIN_SCK 6
#define PIN_MOSI 5
#define PIN_MISO 4

#define HEADER 0x1411
#define DEFAULT_OFFSET 16
#define DIVIDER_OFFSET 288

#define SAMPLING_RATE 0	// 1000 a bit overkill for BMS haha
#define PACKET_SIZE 8800

ADS8688 adc(PIN_CS, PIN_SCK, PIN_MOSI, PIN_MISO);

// Speed Test
// Max rate on board = 160000SPS
// Max rate transfering via serial = 80000SPS

// _attribute_((packed)) forces packet size to be whatever I set. Used prev when 8bit was used but not sure if required now
struct __attribute__((packed)) Packet {
	uint16_t header;
	uint32_t counter;
	uint32_t timediff_us;  // Use micros. Sampling 1 / ms, use us for precision; 32bit -> ~70 min
	uint16_t readings[8];
	uint16_t crc;
};

uint16_t additive_cksum(uint16_t* readings, uint16_t counter) {
	uint16_t sum = counter;
	for (int i = 0; i < 8; i++) {
		sum += readings[i];
	}
	return sum;
}

Packet bulkPackets[PACKET_SIZE];

// Default Vref = 4.096V
// R1: Min = -(1.25 * vref)     = -5.120 V,     Max = +(1.25 * vref)    = +5.120 V
// R5: Min = 0.0 V,                             Max = +(2.5 * vref)     = +10.240 V

const uint8_t R1_SIZE = 6;
const uint8_t R5_SIZE = 2;
const uint8_t r1_pins[R1_SIZE] = { 0, 1, 2, 3, 4, 5 };  // Direct HE sensor reading
const uint8_t r5_pins[R5_SIZE] = { 6, 7 };              // Battery voltage stepped down

uint32_t prevTime_us;
uint32_t counter = 1;
uint16_t packet_position = 0;  // Up to 65536 bulk packet size (Max SRAM only allow ~8k size packet size only)
bool streamEnabled = false;

void checkForStart() {
	if (Serial.available()) {
		String cmd = Serial.readStringUntil('\n');
		if (cmd == "START") {
			Serial.println("ADC Ready");
			Serial.flush();
			streamEnabled = true;
		}
	}
}

uint16_t timer_start = millis();
const uint16_t TIME_TO_ALERT = PACKET_SIZE * 8;
void setup() {
	//Serial.begin(921600);
	Serial.begin(2000000);  // Jtag should ignore the set rate and just do maximum

	for (int i = 0; i < R1_SIZE; i++) {
		adc.setChannelRange(r1_pins[i], R1);
	}

	for (int i = 0; i < R5_SIZE; i++) {
		adc.setChannelRange(r5_pins[i], R5);
	}

	// Enable all 8 channels in auto scan
	adc.setChannelSequence(0xFF);  // or 0b11111111 (not x but b)
	adc.setSampleRate(SAMPLING_RATE);

	// Start auto scan mode
	adc.autoRst();
	adc.autoRst();

	prevTime_us = micros();
	SPI.beginTransaction(SPISettings(ADS8688_SPI_CLOCK, MSBFIRST, SPI_MODE1));

}

uint16_t raw_readings[8];

IRAM_ATTR void loop() {
	if (!streamEnabled) {
		checkForStart();
		return;
	}

	adc.waitForSample();

	while (packet_position < PACKET_SIZE) {
		uint32_t now_us = adc.readAllChannels(raw_readings);
		//uint32_t now_us = micros();

		Packet& currPkt = bulkPackets[packet_position];
		currPkt.header = HEADER;
		currPkt.counter = counter;
		currPkt.timediff_us = now_us - prevTime_us;

		for (int i = 0; i < R1_SIZE; i++) {
			uint8_t idx = r1_pins[i];
			uint16_t raw = raw_readings[idx] - DEFAULT_OFFSET;
			//uint16_t raw = adc.noOpRaw();
			bulkPackets[packet_position].readings[idx] = raw;
			//Serial.printf("CH%d: Raw -> %d  ", idx, raw);
		}

		for (int i = 0; i < R5_SIZE; i++) {
			uint8_t idx = r5_pins[i];
			uint16_t raw = raw_readings[idx];
			//uint16_t raw = adc.noOpRaw();
			if (raw < DIVIDER_OFFSET) {
				raw = 0;
			} else {
				raw -= DIVIDER_OFFSET;
			}
			bulkPackets[packet_position].readings[idx] = raw;
			//Serial.printf("CH%d: Raw -> %d  \n", idx, raw);
		}
		
		currPkt.crc = additive_cksum(currPkt.readings, counter);

		prevTime_us = now_us;
		counter += 1;
		packet_position += 1;
		//Serial.println("=======================");
	}

	if (counter % TIME_TO_ALERT == 1) {
		uint16_t time_now = millis();
		Serial.printf("Time taken to process %d rows * 8 channel = %d\n", TIME_TO_ALERT, time_now - timer_start);
		timer_start = time_now;
	}

	//SPI.endTransaction();

	/* if (!Serial) {
		streamEnabled = false;
		return;
	} 
	Serial.write((uint8_t*)&bulkPackets, sizeof(bulkPackets));
	*/
	
	packet_position = 0;
}