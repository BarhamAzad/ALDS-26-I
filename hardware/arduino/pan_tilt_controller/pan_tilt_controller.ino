#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

const int PAN_CHANNEL = 0;
const int TILT_CHANNEL = 1;

const int SERVO_MIN_US = 1000;
const int SERVO_MAX_US = 2000;
const int SERVO_FREQ = 50;

// Model-space limits:
// 270 = minimum horizontal offset
// 180 = natural horizontal offset
// 90 = maximum horizontal offset
// 0 = maximum vertical offset
// 90 = natural vertical offset
// 150 = minimum vertical offset
const int PAN_MIN = 90;
const int PAN_CENTER = 180;
const int PAN_MAX = 270;
const int TILT_MIN = 80;
const int TILT_CENTER = 90;
const int TILT_MAX = 150;

int currentPan = PAN_CENTER;
int currentTilt = TILT_CENTER;

int angleToPulse(int angle) {
  angle = constrain(angle, 0, 180);
  int pulseUs = map(angle, 0, 180, SERVO_MIN_US, SERVO_MAX_US);
  return (pulseUs * 4096L) / 20000L;
}

int panToServoAngle(int pan) {
  return constrain(pan - PAN_MIN, 0, 180);
}

int tiltToServoAngle(int tilt) {
  return constrain(tilt, 0, 180);
}

int clampCommandValue(float value, int minimum, int maximum) {
  int rounded = value >= 0.0 ? int(value + 0.5) : int(value - 0.5);
  return constrain(rounded, minimum, maximum);
}

void writeServos() {
  pwm.setPWM(PAN_CHANNEL, 0, angleToPulse(panToServoAngle(currentPan)));
  pwm.setPWM(TILT_CHANNEL, 0, angleToPulse(tiltToServoAngle(currentTilt)));
}

void printStatus() {
  Serial.print("PAN:");
  Serial.print(currentPan);
  Serial.print(" TILT:");
  Serial.println(currentTilt);
}

bool readAxisValue(String command, String label, float &value) {
  int valueStart = command.indexOf(label);
  if (valueStart < 0) {
    return false;
  }

  valueStart += label.length();
  int valueEnd = command.indexOf(',', valueStart);
  if (valueEnd < 0) {
    valueEnd = command.length();
  }

  value = command.substring(valueStart, valueEnd).toFloat();
  return true;
}

void handleCommand(String command) {
  command.trim();
  command.toUpperCase();

  if (command.length() == 0) {
    return;
  }

  if (command == "STATUS") {
    printStatus();
    return;
  }

  float panValue = currentPan;
  float tiltValue = currentTilt;
  bool hasPan = readAxisValue(command, "PAN:", panValue);
  bool hasTilt = readAxisValue(command, "TILT:", tiltValue);

  if (!hasPan && !hasTilt) {
    Serial.println("ERR");
    return;
  }

  if (hasPan) {
    currentPan = clampCommandValue(panValue, PAN_MIN, PAN_MAX);
  }
  if (hasTilt) {
    currentTilt = clampCommandValue(tiltValue, TILT_MIN, TILT_MAX);
  }

  writeServos();
  printStatus();
}

void setup() {
  Serial.begin(9600);
  Wire.begin();

  pwm.begin();
  pwm.setPWMFreq(SERVO_FREQ);

  delay(500);
  writeServos();
  printStatus();
}

void loop() {
  if (Serial.available() > 0) {
    handleCommand(Serial.readStringUntil('\n'));
  }
}
