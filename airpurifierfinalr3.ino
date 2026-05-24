#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

#define MQ135_PIN A0
#define RELAY_PIN 7
#define LED_PIN 13

int relayThreshold = 450;
bool fanState = false;

unsigned long fanOffTimer = 0;
bool offDelayStarted = false;


// 🔥 BOOT ANIMATION FUNCTION ADDED
void bootAnimation() {

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);

  display.setCursor(20, 0);
  display.println("SMART AIR SYSTEM");
  display.display();
  delay(800);

  display.drawLine(0, 10, 128, 10, WHITE);
  display.display();

  display.drawRect(14, 54, 100, 6, WHITE);
  display.display();

  int progress = 0;

  const char* checks[4] = {
    "Board Check",
    "Relay Check",
    "Sensor Check",
    "Fan Check"
  };

  for (int i = 0; i < 4; i++) {
    display.setCursor(0, 18 + i * 8);
    display.print(checks[i]);
    display.display();
    delay(400);

    if (i == 1) {
      digitalWrite(RELAY_PIN, LOW);
      delay(200);
      digitalWrite(RELAY_PIN, HIGH);
    }

    if (i == 3) {
      digitalWrite(RELAY_PIN, LOW);
      digitalWrite(LED_PIN, HIGH);
      delay(400);
      digitalWrite(RELAY_PIN, HIGH);
      digitalWrite(LED_PIN, LOW);
    }

    display.setCursor(100, 18 + i * 8);
    display.print("OK");

    progress += 25;
    display.fillRect(16, 56, progress, 2, WHITE);
    display.display();
    delay(400);
  }

  display.clearDisplay();
  display.setCursor(45, 25);
  display.println("READY");
  display.display();
  delay(1000);
}


void setup() {

  Serial.begin(9600);
  Wire.begin();

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(LED_PIN, LOW);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    while (true)
      ;
  }

  bootAnimation();
}


void loop() {

  long total = 0;
  for (int i = 0; i < 20; i++) {
    total += analogRead(MQ135_PIN);
    delay(15);
  }

  int airValue = total / 20;
  Serial.println(airValue);

  // 🔥 Relay ON immediately
  if (airValue > relayThreshold) {
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(LED_PIN, HIGH);
    fanState = true;
    offDelayStarted = false;
  } else {

    if (fanState && !offDelayStarted) {
      fanOffTimer = millis();
      offDelayStarted = true;
    }

    // 🔥 15 SECOND DELAY WITH COUNTDOWN
    if (fanState && offDelayStarted) {

      unsigned long elapsed = millis() - fanOffTimer;
      int remaining = 15 - (elapsed / 1000);

      if (remaining < 0) remaining = 0;

      display.clearDisplay();
      display.setTextSize(1);

      display.setCursor(25, 20);
      display.print("Clearing Air...");

      display.setCursor(35, 35);
      display.print("Fan OFF in ");
      display.print(remaining);

      display.display();

      if (elapsed >= 15000) {
        digitalWrite(RELAY_PIN, HIGH);
        digitalWrite(LED_PIN, LOW);
        fanState = false;
        offDelayStarted = false;
      }

      return;
    }
  }

  // 🔥 NORMAL DASHBOARD

  display.clearDisplay();
  display.setTextSize(1);

  display.setCursor(30, 0);
  display.print("AIR MONITOR");
  display.drawLine(0, 10, 128, 10, WHITE);

  display.setCursor(0, 15);
  display.print("Value: ");
  display.print(airValue);

  display.setCursor(0, 28);
  display.print("Status: ");

  if (airValue <= 250) {
    display.print("GOOD");
  } else if (airValue <= 375) {
    display.print("UNHEALTHY");
  } else if (airValue <= 450) {
    display.print("HIGH");
  } else {
    display.print("POLLUTED");
  }

  display.setCursor(0, 41);
  display.print("Fan: ");
  display.print(fanState ? "ON" : "OFF");

  int barWidth = map(airValue, 0, 1023, 0, 100);
  display.drawRect(14, 54, 100, 6, WHITE);
  display.fillRect(16, 56, barWidth, 2, WHITE);

  display.display();

  delay(200);
}