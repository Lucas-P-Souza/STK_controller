#include <Wire.h>
#include <Digital_Light_TSL2561.h>  // bibliothèque Grove - Digital Light Sensor (TSL2561)

const int sigPin = 7;
const uint8_t TSL2561_ADDR = 0x39;  // adresse I2C par défaut du TSL2561

unsigned long lastLuxRead = 0;
const unsigned long LUX_INTERVAL = 300;  // ne sollicite le bus I2C que toutes les 300ms
int lastLux = -1;
bool tsl2561Present = false;

unsigned long loopCounter = 0;

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
  // laisse le temps au port série de s'établir avant le premier print
  delay(500);
  Serial.println(F("BOOT_OK"));

  Wire.begin();
  Wire.setWireTimeout(3000, true);  // évite tout blocage indéfini du bus I2C

  // diagnostic explicite : le capteur répond-il dès le démarrage ?
  Wire.beginTransmission(TSL2561_ADDR);
  uint8_t err = Wire.endTransmission();
  tsl2561Present = (err == 0);
  Serial.print(F("TSL2561_PRESENT="));
  Serial.println(tsl2561Present ? F("YES") : F("NO"));

  if (tsl2561Present) {
    TSL2561.init();
    Serial.println(F("TSL2561_INIT_DONE"));
  }
}

void loop() {
  loopCounter++;

  long duration = readUltrasonic(sigPin);
  delay(3);  // laisse la ligne SIG se stabiliser avant l'I2C

  if (tsl2561Present) {
    unsigned long now = millis();
    if (now - lastLuxRead >= LUX_INTERVAL) {
      lastLuxRead = now;
      int lux = TSL2561.readVisibleLux();
      if (lux >= 0 && lux < 65535) {
        lastLux = lux;
      }
    }
  }

  // heartbeat + données, à chaque boucle : on veut TOUJOURS voir une ligne,
  // même si une des deux lectures échoue
  Serial.print(loopCounter);
  Serial.print(F(" | dist="));
  if (duration != 0) {
    Serial.print(duration / 58.0);
  } else {
    Serial.print(F("NO_ECHO"));
  }
  Serial.print(F(" | lux="));
  Serial.println(tsl2561Present ? lastLux : -1);

  delay(100);
}
