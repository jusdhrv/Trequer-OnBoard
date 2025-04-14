const int trigPin = 12;  // Trig pin (Ultrasonic)
const int echoPin = 13;  // Echo pin (Ultrasonic)
const int irPin = 14; // IR Pin
const int ldrPin = 23; // LDR Pin
const int mqPin = A3; // MQ4 Pin

const int dhtPin = 27;
#include "DHT.h"
#define DHTTYPE DHT11 // DHT 11
DHT dht(dhtPin, DHTTYPE);

const int safetyDistance = 30;

long duration;  // Travel time in microseconds
int distanceUltrasonic;  // Distance in cm from Ultrasonic
int distanceIR;  // Boolean from IR

int lightIntensity; // Value from LDR

int mqGas; // Value from the MQ4

float humidity;
float tempC;

// Function blocks
int getUltrasonic() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Generate 10-microsecond pulse on Trig pin
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Read Echo pin, returns travel time in microseconds
  duration = pulseIn(echoPin, HIGH);

  return (duration * 0.034 / 2);
}

void setup() {
  pinMode(trigPin, OUTPUT);  // Set Trig pin as output
  pinMode(echoPin, INPUT);  // Set Echo pin as input
  Serial.begin(9600);  // Initialize serial communication

  // Serial.println("DHTxx test!");
  dht.begin();
}

void loop() {
  // Init the current data readout block
  // Serial.println("----------------------------------");

  // Detect if obstacle present
  distanceUltrasonic = getUltrasonic();
  distanceIR = digitalRead(irPin);

  if (distanceUltrasonic <= safetyDistance) {
    // Serial.print("Obstacle at distance (cm): ");
    Serial.print(distanceUltrasonic);
    Serial.print("|");
  }

  if (distanceIR == LOW) {
    // Serial.println("Obstacle detected");
    Serial.print(distanceIR);
    Serial.print("|");
  }

  // Display the light intensity in the environment
  lightIntensity = digitalRead(ldrPin);
  // Serial.print("Light Intensity: ");
  Serial.print(lightIntensity);
  Serial.print("|");

  // Display humidity percentage and temperature
  humidity = dht.readHumidity();
  tempC = dht.readTemperature();
  // Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.print("|");
  // Serial.print("%   Temperature: ");
  Serial.print(tempC);
  Serial.print("|");

  // // Display out from the MQ4
  mqGas = analogRead(mqPin);
  // Serial.print("Methane Concentration: ");
  Serial.print(mqGas);
  Serial.print("\n");

  delay(1000);
}