#include <Wire.h>
#include <Digital_Light_TSL2561.h>  // bibliothèque Grove - Digital Light Sensor (TSL2561)

const int sigPin = 7;


long readUltrasonic(int pin) {
  pinMode(pin, OUTPUT);
  digitalWrite(pin, LOW);
  delayMicroseconds(2);
  digitalWrite(pin, HIGH);
  delayMicroseconds(10);
  digitalWrite(pin, LOW);

  pinMode(pin, INPUT);
  long duration = pulseIn(pin, HIGH, 30000);
  return duration;
}



void setup() {
  Serial.begin(9600);

  Wire.begin();
  TSL2561.init();
}

void loop() {
  int lux = TSL2561.readVisibleLux();
  long duration = readUltrasonic(sigPin);

  float distance_cm = (duration != 0) ? duration / 58.0 : -1.0;

  Serial.print(distance_cm);
  Serial.print(",");
  Serial.println(lux);

  delay(100);
}


