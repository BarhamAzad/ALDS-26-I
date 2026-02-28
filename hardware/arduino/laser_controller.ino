/*
  Zombie Laser Targeting System - Arduino Controller
  Controls laser pan/tilt servos and firing mechanism
  Communication: Serial 9600 baud
*/

#include <Servo.h>

// Pin definitions
const int PAN_SERVO_PIN = 9;
const int TILT_SERVO_PIN = 10;
const int LASER_PIN = 11;
const int FIRE_RELAY_PIN = 12;

// Servo objects
Servo panServo;
Servo tiltServo;

// Current positions
int currentPan = 90;    // 0-180 degrees
int currentTilt = 90;   // 0-180 degrees
bool laserOn = false;
bool fireActive = false;

// Command buffer
String command = "";

void setup() {
  Serial.begin(9600);
  
  // Attach servos
  panServo.attach(PAN_SERVO_PIN);
  tiltServo.attach(TILT_SERVO_PIN);
  
  // Setup laser and fire pins
  pinMode(LASER_PIN, OUTPUT);
  pinMode(FIRE_RELAY_PIN, OUTPUT);
  
  // Initialize servos to center
  panServo.write(90);
  tiltServo.write(90);
  digitalWrite(LASER_PIN, LOW);
  digitalWrite(FIRE_RELAY_PIN, LOW);
  
  Serial.println("Laser Controller Ready");
}

void loop() {
  // Read serial commands
  if (Serial.available() > 0) {
    char inChar = Serial.read();
    
    if (inChar == '\n') {
      processCommand();
      command = "";
    } else {
      command += inChar;
    }
  }
}

void processCommand() {
  command.trim();
  
  if (command.startsWith("PAN:")) {
    // Parse: PAN:45.5,TILT:30.2
    int commaIndex = command.indexOf(',');
    if (commaIndex > 0) {
      String panStr = command.substring(4, commaIndex);
      float panAngle = panStr.toFloat();
      panAngle = constrain(panAngle, 0, 180);
      panServo.write((int)panAngle);
      currentPan = (int)panAngle;
      
      // Parse TILT
      if (command.startsWith("TILT:", commaIndex + 1)) {
        String tiltStr = command.substring(commaIndex + 6);
        float tiltAngle = tiltStr.toFloat();
        tiltAngle = constrain(tiltAngle, 0, 180);
        tiltServo.write((int)tiltAngle);
        currentTilt = (int)tiltAngle;
        
        Serial.print("PAN:");
        Serial.print(currentPan);
        Serial.print(" TILT:");
        Serial.println(currentTilt);
      }
    }
  }
  else if (command == "FIRE:ON") {
    digitalWrite(LASER_PIN, HIGH);
    digitalWrite(FIRE_RELAY_PIN, HIGH);
    fireActive = true;
    Serial.println("FIRING");
  }
  else if (command == "FIRE:OFF") {
    digitalWrite(LASER_PIN, LOW);
    digitalWrite(FIRE_RELAY_PIN, LOW);
    fireActive = false;
    Serial.println("CEASE_FIRE");
  }
  else if (command == "STATUS") {
    Serial.print("PAN:");
    Serial.print(currentPan);
    Serial.print(" TILT:");
    Serial.print(currentTilt);
    Serial.print(" FIRE:");
    Serial.println(fireActive ? "ON" : "OFF");
  }
}
