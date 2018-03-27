#include <Wire.h>
#include <I2Cdev.h>	// https://github.com/jrowberg/i2cdevlib/tree/master/Arduino/I2Cdev
#include <MPU6050_9Axis_MotionApps41.h> // https://github.com/jrowberg/i2cdevlib/tree/master/Arduino/MPU6050

#define FIFO_SIZE 512

MPU6050 mpu;

Quaternion q;           // [w, x, y, z]         quaternion container
float euler[3];         // [psi, theta, phi]    Euler angle container

uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = error)
uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[FIFO_SIZE]; // FIFO storage buffer

volatile bool mpuInterrupt = false;     // indicates whether MPU interrupt pin has gone high


void initMPU()
{
	// initialize device
	mpu.initialize();

	// load and configure the DMP
	devStatus = mpu.dmpInitialize();

	// make sure it worked (returns 0 if so)
	if (devStatus == 0) {
		// turn on the DMP, now that it's ready
		mpu.setDMPEnabled(true);
		mpu.setIntEnabled(0xFF);

		// enable Arduino interrupt detection
		attachInterrupt(0, dmpDataReady, RISING);
		mpuIntStatus = mpu.getIntStatus();

		// get expected DMP packet size for later comparison
		packetSize = mpu.dmpGetFIFOPacketSize();

		// supply your own gyro offsets here, scaled for min sensitivity
		mpu.setXGyroOffset(620);
		mpu.setYGyroOffset(160);
		mpu.setZGyroOffset(-1120);
		mpu.setZAccelOffset(1788); // 1688 factory default for my test chip
	}
	else {
		Serial.print(F("DMP Initialization failed (code "));
		Serial.print(devStatus);
		Serial.println(F(")"));
		while (1);
	}
}

void dmpDataReady()
{
	mpuInterrupt = true;
}

void setup()
{
	// join I2C bus (I2Cdev library doesn't do this automatically)
	Wire.begin();
	TWBR = 24;

	// initialize serial communication
	Serial.begin(115200);

	initMPU();
}

void loop()
{
	// reset interrupt flag and get INT_STATUS byte
	mpuInterrupt = false;
	mpuIntStatus = mpu.getIntStatus();

	// wait for MPU interrupt or extra packet(s) available
	long t_0 = millis();
	while (!mpuInterrupt && fifoCount < packetSize)
		if (millis() - t_0 > 500) {
			initMPU();
			break;
		}

	// get current FIFO count
	fifoCount = mpu.getFIFOCount();

	// check for overflow (this should never happen unless our code is too inefficient)
	if ((mpuIntStatus & 0x10) && fifoCount > 0) {
		// reset so we can continue cleanly
		Serial.print(fifoCount);
		Serial.println(F(" FIFO overflow!"));

		mpu.resetFIFO();
		fifoCount = 0;
		// otherwise, check for DMP data ready interrupt (this should happen frequently)
	}
	else if ((mpuIntStatus & 0x01 || mpuInterrupt) && fifoCount > 0) {
		// wait for correct available data length, should be a VERY short wait
		long t_0 = millis();
		while (fifoCount < packetSize) {
			fifoCount = mpu.getFIFOCount();
			if (millis() - t_0 > 200) {
				initMPU();
				break;
		}
	}

	// read a packet from FIFO
	mpu.getFIFOBytes(fifoBuffer, packetSize);

	// track FIFO count here in case there is > 1 packet available
	// (this lets us immediately read more without waiting for an interrupt)
	fifoCount -= packetSize;

	// display Euler angles in degrees
	mpu.dmpGetQuaternion(&q, fifoBuffer);
	Serial.println(q.w);
	// mpu.dmpGetEuler(euler, &q);
	// Serial.print('euler\t');
	// Serial.print(euler[0] * 180 / M_PI);
	// Serial.print(',');
	// Serial.println(euler[1] * 180 / M_PI);
	// Serial.print(',');
	// Serial.println(euler[2] * 180 / M_PI);
	}
}
