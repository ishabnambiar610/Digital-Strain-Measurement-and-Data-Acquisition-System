#include "HX711.h"

HX711 scale;

uint8_t dataPin = 16;
uint8_t clockPin = 17;

// ==== USER CONSTANTS ====

// Beam geometry
const float L = 0.15569;     // meters
const float b = 0.00318;     // meters
const float t = 0.02381;     // meters

// Material (example: Aluminium or Steel — CHANGE THIS!)
const float E = 2.0e11;      // Pa (Steel ~200 GPa)

// Strain gauge
const float GF = 2.0;

// =======================

float weight;   // from HX711 (kg or N depending calibration)
float strain;

void setup()
{
  Serial.begin(115200);

  scale.begin(dataPin, clockPin);

  scale.set_scale(420.0983);   // your calibration
  scale.tare();
}

void loop()
{
  // Read weight
  weight = scale.get_units(5);

  // If calibration gives kg → convert to Newton
  float W = weight * 9.81;

  // Strain formula
  strain = (6 * W * L) / (E * b * t * t);

  Serial.print("Weight (kg): ");
  Serial.print(weight);

  Serial.print("   Strain: ");
  Serial.println(strain, 10);  // high precision

  delay(250);
}