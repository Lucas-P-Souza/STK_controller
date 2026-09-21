const int bt1 = 8;
const int bt2 = 7;
const int bt3 = 4;
const int buzzerPin = 5;

const int led1 = 9;
const int led2 = 10;
const int led3 = 11;

const int moteur = A0;
const int wheel = 12;

const int usPin = 2;


int value1 = 0;
int value2 = 0;
int value3 = 0;

bool state1 = false;
bool state2 = false;
bool state3 = false;

void randomiserValeurs() {
  value1 = random(1, 10);
  value2 = random(1, 10);
  value3 = random(1, 10);
}

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
  pinMode(bt1, INPUT_PULLUP);
  pinMode(bt2, INPUT_PULLUP);
  pinMode(bt3, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);
  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(led3, OUTPUT);
  pinMode(wheel, OUTPUT);
  pinMode(usPin, OUTPUT);

  randomSeed(analogRead(A1)); // A0 étant utilisé pour "moteur", on prend A1 comme graine
  randomiserValeurs();
}

void loop() {
  long duration = readUltrasonic(usPin);
  float distance_cm = (duration != 0) ? duration / 58.0 : -1.0;
  Serial.print(distance_cm);
  Serial.print(",");

  int etat1 = digitalRead(bt1);
  int etat2 = digitalRead(bt2);
  int etat3 = digitalRead(bt3);
  int moteur_value = analogRead(moteur);

  // Bouton 1
  if (etat1 == LOW && !state1 && value1 > 0) {
    value1 -= 1;
    state1 = true;
  } else if (etat1 == HIGH) {
    state1 = false;
  }

  // Bouton 2
  if (etat2 == LOW && !state2 && value2 > 0) {
    value2 -= 1;
    state2 = true;
  } else if (etat2 == HIGH) {
    state2 = false;
  }

  // Bouton 3
  if (etat3 == LOW && !state3 && value3 > 0) {
    value3 -= 1;
    state3 = true;
  } else if (etat3 == HIGH) {
    state3 = false;
  }

  // Réinitialisation quand les 3 valeurs sont à 0
  if (value1 == 0 && value2 == 0 && value3 == 0) {
    randomiserValeurs();
    tone(buzzerPin, 100, 500);
    digitalWrite(led1, 1);
    digitalWrite(led2, 1);
    digitalWrite(led3, 1);
    delay(200);
    digitalWrite(led1, 0);
    digitalWrite(led2, 0);
    digitalWrite(led3, 0);
    delay(200);
    digitalWrite(led1, 1);
    digitalWrite(led2, 1);
    digitalWrite(led3, 1);
    delay(200);
    digitalWrite(led1, 0);
    digitalWrite(led2, 0);
    digitalWrite(led3, 0);
    delay(200);
    digitalWrite(led1, 1);
    digitalWrite(led2, 1);
    digitalWrite(led3, 1);
    delay(200);
    Serial.print(1);
  } else {
    Serial.print(0);
  }
  Serial.print(",");

  digitalWrite(led1, value1 == 0);
  digitalWrite(led2, value2 == 0);
  digitalWrite(led3, value3 == 0);

  if (moteur_value > 0) {
    Serial.println(1);
    digitalWrite(wheel, 1);
  } else {
    Serial.println(0);
    digitalWrite(wheel, 0);
  }

  // Pour le moment on ne peut pas utiliser le digit,
  // donc on utilise des LEDs pour que quand une valeur est à 0, sa LED s'allume

  delay(20);
}