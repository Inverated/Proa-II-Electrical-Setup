#include <ADS8688.h>

#define PIN_CS 7
#define PIN_SCK 6
#define PIN_MOSI 5
#define PIN_MISO 4

#define DEFAULT_OFFSET 16
#define DIVIDER_OFFSET 288

#define SAMPLING_RATE 0
#define PACKET_SIZE 5
// Stupid ESP32 C3. CDC doesent work, takes 120ms for 1000 packet size
// Since single core, cannot read from adc while writing
// Max recorded transfer speed 630KB/s (163kSPS)
// Pkt size = 5, Flushing into CSV at 1000 count, reading at 5-50 packets
// Max benchmark without serial write 5000 rows * 8 ch = 155ms (258kSPS)

#define TIME_TO_ALERT PACKET_SIZE	// Logging speed test (LOGGING & TRANSNMITTING = 0)

#define LOGGING 			0
#define TRANSMITTING 	1
#define BAUD_RATE 2000000
#define ADS8688_SPI_CLOCK 20000000  // Overide library. Datasheet max 17M; Stable until 30M

#define HEADER 0xDEADBEEF

ADS8688 adc(PIN_CS, PIN_SCK, PIN_MOSI, PIN_MISO);

struct __attribute__((packed)) Packet {
	uint32_t header;
	uint16_t counter;
	uint32_t timediff_us;
	uint16_t readings[8];
	uint16_t chksum;
};

uint16_t additive_chksum(uint16_t* readings, uint16_t counter) {
	uint16_t sum = counter;
	for (int i = 0; i < 8; i++) {
		sum += readings[i] * (i + 1);
	}
	return sum;
}

Packet bulkPacket[PACKET_SIZE];

// Default Vref = 4.096V
// R1: Min = -(1.25 * vref)     = -5.120 V,     Max = +(1.25 * vref)    = +5.120 V
// R5: Min = 0.0 V,                             Max = +(2.5 * vref)     = +10.240 V

const uint8_t R1_SIZE = 6;
const uint8_t R5_SIZE = 2;
const uint8_t r1_pins[R1_SIZE] = { 0, 1, 2, 3, 4, 5 };  // Direct HE sensor reading
const uint8_t r5_pins[R5_SIZE] = { 6, 7 };              // Battery voltage stepped down

uint16_t raw_readings[8];
uint32_t prevTime_us;
uint16_t counter = 1;
uint16_t packet_position = 0;
uint16_t timer_start;
bool streamEnabled = false;

void checkForStart() {
	if (Serial.available()) {
		String cmd = Serial.readStringUntil('\n');
		if (cmd == "START") {
			Serial.println("ADC Ready");
			streamEnabled = true;
		}
	}
}


void setup() {
	Serial.begin(BAUD_RATE);

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

	SPI.beginTransaction(SPISettings(ADS8688_SPI_CLOCK, MSBFIRST, SPI_MODE1));

	prevTime_us = micros();
	timer_start = millis();
}


IRAM_ATTR void loop() {
	if (!streamEnabled) {
		checkForStart();
		return;
	}

	while (packet_position < PACKET_SIZE) {
		adc.waitForSample();  // Limit sampling rate. If sampling rate set to 0, no effect

		uint32_t now_us = adc.readAllChannels(raw_readings);

		Packet& currPkt = bulkPacket[packet_position];
		currPkt.counter = counter;
		currPkt.timediff_us = now_us - prevTime_us;

		for (int i = 0; i < R1_SIZE; i++) {
			uint8_t idx = r1_pins[i];
			uint16_t raw = raw_readings[idx] - DEFAULT_OFFSET;

#if LOGGING && !TRANSMITTING
			Serial.printf("CH%d: Raw -> %d  ", idx, raw);
#endif

			currPkt.readings[idx] = raw;
		}

		for (int i = 0; i < R5_SIZE; i++) {
			uint8_t idx = r5_pins[i];
			uint16_t raw = raw_readings[idx];

			if (raw < DIVIDER_OFFSET) {
				raw = 0;
			} else {
				raw -= DIVIDER_OFFSET;
			}
			currPkt.readings[idx] = raw;

#if LOGGING && !TRANSMITTING
			Serial.printf("CH%d: Raw -> %d  \n", idx, raw);
#endif
		}

		currPkt.chksum = additive_chksum(currPkt.readings, counter);
		currPkt.header = HEADER;

		prevTime_us = now_us;
		if (counter == 65535) {
			counter = 1;
		} else {
			counter += 1;
		}
		packet_position += 1;
#if LOGGING && !TRANSMITTING
		Serial.println("=======================");
#endif
	}

	if (!LOGGING && !TRANSMITTING && counter % TIME_TO_ALERT == 1) {
		uint16_t time_now = millis();
		Serial.printf("Time taken to process %d rows * 8 channel = %d\n", TIME_TO_ALERT, time_now - timer_start);
		timer_start = time_now;
	}

	if (TRANSMITTING && !Serial) {
		streamEnabled = false;
		return;
	}

#if TRANSMITTING
	Serial.write((uint8_t*)bulkPacket, sizeof(bulkPacket));
#endif

	packet_position = 0;
}