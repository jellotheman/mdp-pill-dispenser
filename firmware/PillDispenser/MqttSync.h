#pragma once
// Disposable Wokwi demonstration transport. The controller and persistent store
// remain on the main task; MQTT and its blocking reconnect run on a worker.
#include <WiFi.h>
#include <PubSubClient.h>

class MqttSync {
  struct Message { char body[6144]; };
  struct Job { bool configAck; char body[6144]; };
  QueueHandle_t configs_ = nullptr, receipts_ = nullptr, jobs_ = nullptr;
  uint64_t nextAck_ = 0, nextEvent_ = 0;
  mdp::Text latestConfig_, latestAck_;
  String configTopic_, configAckTopic_, eventTopic_, receiptTopic_;
  WiFiClient socket_;
  PubSubClient client_{socket_};
  inline static MqttSync* instance_ = nullptr;
  static void worker(void* self) { static_cast<MqttSync*>(self)->work(); }
  static void received(char* topic, byte* payload, unsigned length) {
    if (instance_) instance_->receive(topic, payload, length);
  }
  void receive(const char* topic, const byte* payload, unsigned length) {
    if (length >= sizeof(Message::body)) return;
    static Message message; // Avoid placing a 6 KB message on the worker stack.
    memcpy(message.body, payload, length); message.body[length] = 0;
    if (configTopic_ == topic) xQueueOverwrite(configs_, &message);
    else if (receiptTopic_ == topic) xQueueOverwrite(receipts_, &message);
  }
  void work() {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    client_.setServer(MQTT_HOST, MQTT_PORT);
    client_.setCallback(received);
    client_.setBufferSize(6500);
    client_.setSocketTimeout(2);
    auto* job = new Job;
    uint32_t retry = 0;
    for (;;) {
      if (WiFi.status() != WL_CONNECTED) {
        vTaskDelay(pdMS_TO_TICKS(500));
        continue;
      }
      if (!client_.connected()) {
        if (static_cast<int32_t>(millis() - retry) < 0) { vTaskDelay(pdMS_TO_TICKS(100)); continue; }
        retry = millis() + 3000;
        String id = String("mdp-") + String(esp_random(), HEX);
        bool ok = strlen(MQTT_USERNAME) ? client_.connect(id.c_str(), MQTT_USERNAME, MQTT_PASSWORD) : client_.connect(id.c_str());
        if (!ok) { vTaskDelay(pdMS_TO_TICKS(100)); continue; }
        client_.subscribe(configTopic_.c_str(), 1);
        client_.subscribe(receiptTopic_.c_str(), 1);
        Serial.println("MQTT connected (public demo; untrusted data)");
      }
      client_.loop();
      if (xQueueReceive(jobs_, job, 0) == pdTRUE)
        client_.publish(job->configAck ? configAckTopic_.c_str() : eventTopic_.c_str(), job->body, false);
      vTaskDelay(pdMS_TO_TICKS(20));
    }
  }
  bool send(bool ack, const mdp::Text& body) {
    if (body.size() >= sizeof(Job::body)) return false;
    static Job job;
    job.configAck = ack;
    snprintf(job.body, sizeof(job.body), "%s", body.c_str());
    return xQueueSend(jobs_, &job, 0) == pdTRUE;
  }
 public:
  bool begin() {
    if (!ENABLE_NETWORK) return true;
    // A public broker cannot establish message authenticity. Never enable on hardware.
    if (!SIMULATION_PROFILE || !strlen(MQTT_HOST) || !mdp::identifier(MQTT_NAMESPACE) || !mdp::identifier(DEVICE_ID)) return false;
    String base = String("mdp-demo/") + MQTT_NAMESPACE + "/" + DEVICE_ID + "/";
    configTopic_ = base + "config"; configAckTopic_ = base + "config-ack";
    eventTopic_ = base + "events"; receiptTopic_ = base + "event-ack";
    configs_ = xQueueCreate(1, sizeof(Message)); receipts_ = xQueueCreate(1, sizeof(Message)); jobs_ = xQueueCreate(1, sizeof(Job));
    instance_ = this;
    if (configs_ && receipts_ && jobs_ && xTaskCreate(worker, "mdp-mqtt", 8192, this, 1, nullptr) == pdPASS) return true;
    if (configs_) vQueueDelete(configs_); if (receipts_) vQueueDelete(receipts_); if (jobs_) vQueueDelete(jobs_);
    configs_ = receipts_ = jobs_ = nullptr; instance_ = nullptr;
    return false;
  }
  void pump(mdp::Controller& controller, uint64_t now) {
    if (!ENABLE_NETWORK || !configs_ || !receipts_ || !jobs_) return;
    static Message message;
    if (xQueueReceive(configs_, &message, 0) == pdTRUE) {
      latestConfig_ = message.body;
      nextAck_ = 0;
    }
    if (xQueueReceive(receipts_, &message, 0) == pdTRUE) {
      JsonDocument receipt;
      if (!deserializeJson(receipt, message.body) && receipt["accepted"] == true && receipt["event_id"].is<const char*>()) {
        mdp::Text id = receipt["event_id"].as<mdp::Text>();
        // Only an outstanding event may be acknowledged. Public demo data is untrusted.
        if (controller.store.data["pending"].size() && controller.store.data["pending"][0]["event_id"].as<mdp::Text>() == id)
          if (!controller.store.acknowledge(id)) controller.fail("storage_failed");
      }
    }
    if (!latestConfig_.empty() && now >= nextAck_) {
      JsonDocument config;
      if (!deserializeJson(config, latestConfig_)) {
        mdp::Text result = controller.applyConfig(config.as<JsonVariantConst>());
        JsonDocument ack;
        ack["revision"] = config["revision"];
        ack["status"] = result == "applied" || result == "unchanged" ? "applied" : result == "deferred" ? "deferred" : "rejected";
        ack["reason"] = result;
        latestAck_.clear(); serializeJson(ack, latestAck_);
        send(true, latestAck_);
      }
      nextAck_ = now + 5000;
    }
    if (now >= nextEvent_ && controller.store.data["pending"].size()) {
      mdp::Text event; serializeJson(controller.store.data["pending"][0], event);
      if (event.size() >= sizeof(Job::body)) controller.fail("event_too_large");
      else if (send(false, event)) nextEvent_ = now + 2000;
    }
  }
};
