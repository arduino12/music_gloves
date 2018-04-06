#include <Wire.h>


#define MPU6050_I2C_ADDR		(0x68)
#define MPU6050_SMPLRT_DIV		(0x19)
#define MPU6050_CONFIG			(0x1A)
#define MPU6050_GYRO_CONFIG		(0x1B)
#define MPU6050_ACCEL_CONFIG	(0x1C)
#define MPU6050_RAW_READ_START	(0x3B)
#define MPU6050_PWR_MGMT_1		(0x6B)
#define MPU6050_WHO_AM_I		(0x75)

#define ACC_COEF				(0.98)
#define GYRO_COEF				(0.02)

/* 32768 / 2 */
#define ACC_RAW					(16384.0)
/* 32768 / 250 */
#define GYRO_RAW				(131.0)


float mpu6050_acc_x, mpu6050_acc_y, mpu6050_acc_z;
float mpu6050_gyro_x, mpu6050_gyro_y, mpu6050_gyro_z;
float mpu6050_gyro_angle_x, mpu6050_gyro_angle_y, mpu6050_gyro_angle_z;
float mpu6050_angle_x, mpu6050_angle_y, mpu6050_angle_z, mpu6050_temp;
uint32_t mpu6050_last_read_millis;


void mpu6050_write(uint8_t reg, uint8_t data)
{
	Wire.beginTransmission(MPU6050_I2C_ADDR);
	Wire.write(reg);
	Wire.write(data);
	Wire.endTransmission();
}

void mpu6050_read()
{
	int16_t raw_acc_x, raw_acc_y, raw_acc_z, raw_temp, raw_gyro_x, raw_gyro_y, raw_gyro_z;
	float dt, angle_acc_x, angle_acc_y, acc_z2;

	dt = (millis() - mpu6050_last_read_millis) / 1000.0;
	mpu6050_last_read_millis = millis();
	
	Wire.beginTransmission(MPU6050_I2C_ADDR);
	Wire.write(MPU6050_RAW_READ_START);
	Wire.endTransmission(false);
	Wire.requestFrom(MPU6050_I2C_ADDR, 14, (int)true);
	
	raw_acc_x = Wire.read() << 8 | Wire.read();
	raw_acc_y = Wire.read() << 8 | Wire.read();
	raw_acc_z = Wire.read() << 8 | Wire.read();
	raw_temp = Wire.read() << 8 | Wire.read();
	raw_gyro_x = Wire.read() << 8 | Wire.read();
	raw_gyro_y = Wire.read() << 8 | Wire.read();
	raw_gyro_z = Wire.read() << 8 | Wire.read();

	/* read temperature in celsius degrees */
	mpu6050_temp = (raw_temp + 12412.0) / 340.0;

	mpu6050_acc_x = raw_acc_x / ACC_RAW;
	mpu6050_acc_y = raw_acc_y / ACC_RAW;
	mpu6050_acc_z = raw_acc_z / ACC_RAW;

	mpu6050_gyro_x = raw_gyro_x / GYRO_RAW;
	mpu6050_gyro_y = raw_gyro_y / GYRO_RAW;
	mpu6050_gyro_z = raw_gyro_z / GYRO_RAW;

	// angle_acc_x = atan2(mpu6050_acc_y, mpu6050_acc_z + abs(mpu6050_acc_x)) * 180 / PI;
	// angle_acc_y = atan2(mpu6050_acc_x, mpu6050_acc_z + abs(mpu6050_acc_y)) * -180 / PI;
	acc_z2 = mpu6050_acc_z * mpu6050_acc_z;
	angle_acc_x = atan(mpu6050_acc_y / sqrt(mpu6050_acc_x * mpu6050_acc_x + acc_z2)) * RAD_TO_DEG;
	angle_acc_y = atan(-mpu6050_acc_x / sqrt(mpu6050_acc_y * mpu6050_acc_y + acc_z2)) * RAD_TO_DEG;

	mpu6050_gyro_angle_x = mpu6050_gyro_x * dt;
	mpu6050_gyro_angle_y = mpu6050_gyro_y * dt;
	mpu6050_gyro_angle_z = mpu6050_gyro_z * dt;

	// mpu6050_angle_x = gyro_coef * mpu6050_gyro_angle_x + acc_coef * angle_acc_x;
	// mpu6050_angle_y = gyro_coef * mpu6050_gyro_angle_y + acc_coef * angle_acc_y;
	mpu6050_angle_x = GYRO_COEF * angle_acc_x + ACC_COEF * (mpu6050_angle_x + mpu6050_gyro_angle_x);
	mpu6050_angle_y = GYRO_COEF * angle_acc_y + ACC_COEF * (mpu6050_angle_y + mpu6050_gyro_angle_y);
	mpu6050_angle_z = mpu6050_gyro_angle_z + mpu6050_angle_z;
}

void mpu6050_init()
{
	Wire.begin();
	// mpu6050_write(MPU6050_SMPLRT_DIV, 0x00);
	// mpu6050_write(MPU6050_CONFIG, 0x00);
	// mpu6050_write(MPU6050_GYRO_CONFIG, 0x08);
	// mpu6050_write(MPU6050_ACCEL_CONFIG, 0x00);
	// mpu6050_write(MPU6050_PWR_MGMT_1, 0x01);
	mpu6050_write(MPU6050_PWR_MGMT_1, 0x00);
	mpu6050_last_read_millis = millis();
	mpu6050_read();
}
