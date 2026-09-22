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


}



void loop() {
  long duration = readUltrasonic(sigPin);

  float distance_cm = (duration != 0) ? duration / 58.0 : -1.0;

  Serial.println(distance_cm);

  delay(100);
}