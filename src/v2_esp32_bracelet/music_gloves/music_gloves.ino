#include <BluetoothSerial.h> // https://github.com/espressif/arduino-esp32
#include "mpu6050_lite.h"


/* uart baud rate in bit per seconds */
#define SERIAL_BAUD_RATE		(115200)
/* uart read timeout in milliseconds */
#define SERIAL_TIMEOUT			(1)
/* bluetooth serial device name */
#define BT_SERIAL_NAME			("Music Gloves")

#define FAST_OUTPUT_INTERVAL	(30)
#define SLOW_OUTPUT_INTERVAL	(70)


enum output_data_format_e {
	RAW_DATA_FORMAT,
	X_ANGLE_DATA_FORMAT,
	Y_ANGLE_DATA_FORMAT,
	XY_ANGLE_DATA_FORMAT,
	XYZ_ANGLE_DATA_FORMAT,
};

BluetoothSerial bt_serial;

uint8_t output_data_format = XY_ANGLE_DATA_FORMAT;
uint16_t output_interval_ms = SLOW_OUTPUT_INTERVAL;
uint32_t next_output_ms;


void read_input_command()
{
	char c = '\0';

	/*
		BluetoothSerial BUG (as of 06/04/18):
		Starting from the first received byte,
		all transmited bytes will slow down after about 10 seconds...
		Quick fix is to send another one each 5 seconds..
	*/
	if (bt_serial.available()) {
		c = bt_serial.read();
	}
	
	if (Serial.available()) {
		c = Serial.read();
	}

	switch (c) {
	case 'A':
		output_data_format = RAW_DATA_FORMAT;
		break;
	case 'B':
		output_data_format = X_ANGLE_DATA_FORMAT;
		break;
	case 'C':
		output_data_format = Y_ANGLE_DATA_FORMAT;
		break;
	case 'D':
		output_data_format = XY_ANGLE_DATA_FORMAT;
		break;
	case 'E':
		output_data_format = XYZ_ANGLE_DATA_FORMAT;
		break;
	case 'F':
		output_interval_ms = FAST_OUTPUT_INTERVAL;
		break;
	case 'G':
		output_interval_ms = SLOW_OUTPUT_INTERVAL;
		break;
	}
}

void write_output_data()
{
	char buf[60];

	switch (output_data_format) {
	case RAW_DATA_FORMAT:
		sprintf(buf, "%03.02f,%03.02f,%03.02f,%03.02f,%03.02f,%03.02f",
			mpu6050_acc_x, mpu6050_acc_y, mpu6050_acc_z, 
			mpu6050_gyro_angle_x, mpu6050_gyro_angle_y, mpu6050_gyro_angle_z);
		break;
	case X_ANGLE_DATA_FORMAT:
		sprintf(buf, "%03.02f", mpu6050_angle_x);
		break;
	case Y_ANGLE_DATA_FORMAT:
		sprintf(buf, "%03.02f", mpu6050_angle_y);
		break;
	case XY_ANGLE_DATA_FORMAT:
		sprintf(buf, "%03.02f,%03.02f", mpu6050_angle_x, mpu6050_angle_y);
		break;
	case XYZ_ANGLE_DATA_FORMAT:
		sprintf(buf, "%03.02f,%03.02f,%03.02f", mpu6050_angle_x, mpu6050_angle_y, mpu6050_angle_z);
		break;
	}

	Serial.println(buf);
	bt_serial.println(buf);
}

void setup()
{
	/* initialize usb serial (uart) communication */
	Serial.begin(SERIAL_BAUD_RATE);
	Serial.setTimeout(SERIAL_TIMEOUT);

	/* initialize mpu6050 sensor */
	mpu6050_init();

	/* initialize bluetooth serial communication */
	bt_serial.begin(BT_SERIAL_NAME);
}

void loop()
{
	uint32_t cur_ms = millis();

	/* read user command from bt or usb serial */
	read_input_command();

	/* update mpu6050 readings */
	mpu6050_read();

	/* write output data to bt and usb serial if needed */
	if (cur_ms > next_output_ms) {
		next_output_ms = cur_ms + output_interval_ms;
		write_output_data();
	}

	yield();
	delay(5);
}

