// MDP ESP32 dispenser. See firmware/README.md and docs/ARCHITECTURE.md.
// Install the versions listed in libraries.txt through Wokwi/Arduino Library Manager.
#include <Arduino.h>
#include <Preferences.h>
#include <ESP32Servo.h>
#include <RTClib.h>
#include "settings.h"
#include "DispenserCore.h"
#include "HttpSync.h"
#if defined(MDP_MQTT_ENABLED) && MDP_MQTT_ENABLED
#include "MqttSync.h"
#endif

constexpr int SERVO_PIN = 18, VALID_PIN = 19, INVALID_PIN = 23, DROP_PIN = 32;
constexpr int RED_LED = 26, GREEN_LED = 27, BUZZER_PIN = 25;

class NvsPersistence : public mdp::Persistence {
 public:
  Preferences preferences;
  bool opened = false;
  Load load(JsonDocument& doc) override {
    opened = preferences.begin("mdp-v2", false);
    if (!opened) return Broken;
    if (!preferences.isKey("state")) return Fresh;
    String saved = preferences.getString("state", "");
    return saved.length() && !deserializeJson(doc, saved) ? Loaded : Broken;
  }
  bool save(const JsonDocument& doc) override {
    if (!opened) return false;
    String saved;
    serializeJson(doc, saved);
    return preferences.putString("state", saved) > 0 &&
           preferences.getString("state", "") == saved;
  }
};

struct Button {
  int pin; bool raw = true, stable = true; uint64_t changed = 0;
  explicit Button(int p) : pin(p) {}
  void begin() { pinMode(pin, INPUT_PULLUP); raw = stable = digitalRead(pin); }
  bool pressed(uint64_t now) {
    bool value = digitalRead(pin);
    if (value != raw) { raw = value; changed = now; }
    if (value != stable && now - changed >= 40) { stable = value; return !value; }
    return false;
  }
};

class WokwiMechanism : public mdp::Simulation {
 public:
  Servo servo;
  void begin() { servo.setPeriodHertz(50); servo.attach(SERVO_PIN, 500, 2500); servo.write(0); }
  bool sensorClear() override { return digitalRead(DROP_PIN) == HIGH; }
 protected:
  void gate(bool open) override { servo.write(open ? 90 : 0); }
};

NvsPersistence persistence;
WokwiMechanism simulation;
mdp::UnconfiguredMechanism physical;
mdp::Store* storage = nullptr;
mdp::Controller* controller = nullptr;
#if defined(MDP_MQTT_ENABLED) && MDP_MQTT_ENABLED
MqttSync syncClient;
#else
HttpSync syncClient;
#endif
RTC_DS1307 rtc;
Button validButton(VALID_PIN), invalidButton(INVALID_PIN), dropButton(DROP_PIN);
uint64_t elapsed = 0, lastClock = 0;
uint32_t previousMillis = 0;
String serialLine;

void printEvent(const JsonDocument& event) {
  serializeJson(event, Serial);
  Serial.println();
}

void serialInput() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\r') continue;
    if (ch != '\n') {
      if (serialLine.length() < 6144) serialLine += ch;
      else { serialLine = ""; Serial.println("serial command too long"); }
      continue;
    }
    if (SIMULATION_PROFILE && serialLine == "erase-demo") {
      // Explicit local command for disposable simulations only. Never automatic.
      persistence.preferences.clear();
      Serial.println("Disposable simulation state erased; restarting.");
      Serial.flush(); ESP.restart();
    }
    JsonDocument command;
    if (!deserializeJson(command, serialLine) && command["command"] == "apply_config") {
      mdp::Text result = controller->applyConfig(command["config"]);
      JsonDocument reply;
      reply["event"] = "config_result"; reply["result"] = result;
      reply["revision"] = storage->data["config"]["revision"];
      printEvent(reply);
    }
    serialLine = "";
  }
}

void setup() {
  Serial.begin(115200);
  validButton.begin(); invalidButton.begin(); dropButton.begin();
  pinMode(RED_LED, OUTPUT); pinMode(GREEN_LED, OUTPUT); pinMode(BUZZER_PIN, OUTPUT);
  char session[24];
  snprintf(session, sizeof(session), "%08lx%08lx",
           static_cast<unsigned long>(esp_random()), static_cast<unsigned long>(esp_random()));
  storage = new mdp::Store(persistence, DEVICE_ID, session);
  storage->begin(SIMULATION_PROFILE);
  // No physical driver is selected or attached by setting a flag.
  if (SIMULATION_PROFILE) simulation.begin();
  controller = new mdp::Controller(SIMULATION_PROFILE ? static_cast<mdp::Mechanism&>(simulation) :
                                                       static_cast<mdp::Mechanism&>(physical),
                                    *storage, printEvent);
  controller->begin();
  if (!DEMO_TIMERS) {
    Wire.begin(21, 22); Wire.setTimeOut(20);
    if (!rtc.begin() || !rtc.isrunning()) controller->fail("rtc_unavailable_or_stopped");
  }
  if (!syncClient.begin()) Serial.println("network settings incomplete; local operation only");
  Serial.println("Simulation profile: buttons represent user 1, rejected user, and one passage.");
  Serial.println("Virtual homing/indexing are logged; the servo visualizes release only.");
  if (DEMO_TIMERS) Serial.println("Demo timers: 5s / 35s / 65s.");
  else Serial.println("Daily schedules use the simulated RTC.");
  Serial.println("Type erase-demo only to reset disposable simulation data.");
  previousMillis = millis();
}

void loop() {
  uint32_t current = millis();
  elapsed += static_cast<uint32_t>(current - previousMillis);
  previousMillis = current;
  bool good = validButton.pressed(elapsed);
  bool bad = invalidButton.pressed(elapsed);
  bool passage = dropButton.pressed(elapsed);
  controller->tick(elapsed);

  if (SIMULATION_PROFILE && DEMO_TIMERS) {
    const uint64_t at[] = {5000, 35000, 65000};
    for (unsigned i = 0; i < 3; ++i) {
      if (elapsed < at[i]) continue;
      mdp::Text id = "demo" + std::to_string(i + 1);
      mdp::Dose dose{"demo-day:" + id, id, i + 1, 1, 0};
      if (controller->offer(dose, elapsed, int64_t(mdp::AUTH_MS) - int64_t(elapsed - at[i]))) break;
    }
  } else if (controller->idle() && elapsed - lastClock >= 1000) {
    lastClock = elapsed;
    DateTime clock = rtc.now();
    if (!clock.isValid() || !rtc.isrunning()) controller->fail("invalid_rtc");
    else {
      char date[12];
      snprintf(date, sizeof(date), "%04u-%02u-%02u", clock.year(), clock.month(), clock.day());
      mdp::offerDaily(*controller, date, clock.hour()*3600u + clock.minute()*60u + clock.second(), elapsed);
    }
  }

  // Conflicting biometric signals count as a rejection. Held inputs never repeat.
  if (bad) controller->authenticate(0, elapsed);
  else if (good) controller->authenticate(1, elapsed);
  if (passage) controller->passage(elapsed);
  serialInput();
  syncClient.pump(*controller, elapsed);

  bool waiting = controller->phase == mdp::Phase::Waiting;
  bool pulse = waiting && elapsed % 1000 < 200;
  digitalWrite(RED_LED, pulse || controller->phase == mdp::Phase::Error || controller->phase == mdp::Phase::Missed);
  digitalWrite(GREEN_LED, controller->phase == mdp::Phase::Completed);
  if (pulse) tone(BUZZER_PIN, 1500); else noTone(BUZZER_PIN);
  delay(5);
}
