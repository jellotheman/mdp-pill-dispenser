#pragma once
// HTTPClient is synchronous, so it runs ONLY in a separate ESP32 task.
// Queues carry copied strings; the task never touches Controller, JsonDocument,
// Preferences, sensors, or actuators.
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ctime>

class HttpSync {
  enum Kind { Config, ConfigAck, Event };
  struct Job { Kind kind; char body[6144]; char eventId[128]; };
  struct Reply { Kind kind; int status; char body[6144]; char eventId[128]; };
  QueueHandle_t jobs_ = nullptr, replies_ = nullptr;
  bool inFlight_ = false;
  uint64_t nextConfig_ = 0, retryAt_ = 0;
  mdp::Text pendingAck_;
  static void worker(void* argument) { static_cast<HttpSync*>(argument)->work(); }

  void work() {
    auto* job = new Job;
    auto* reply = new Reply;
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    configTime(0, 0, "pool.ntp.org");
    for (;;) {
      if (xQueueReceive(jobs_, job, portMAX_DELAY) != pdTRUE) continue;
      reply->kind = job->kind; reply->status = -1;
      reply->body[0] = 0;
      snprintf(reply->eventId, sizeof(reply->eventId), "%s", job->eventId);
      if (WiFi.status() != WL_CONNECTED) {
        WiFi.reconnect();
      } else {
        String url = String(BACKEND_URL) + "/api/v1/devices/" + DEVICE_ID +
                     (job->kind == Config ? "/config" : job->kind == Event ? "/events" : "/config-acks");
        HTTPClient http;
        WiFiClient plain;
        WiFiClientSecure secure;
        const bool https = url.startsWith("https://");
        bool allowed = true;
        if (https) {
          // Do not turn certificate checks off to make a demonstration pass.
          allowed = strlen(BACKEND_ROOT_CA) && time(nullptr) > 1700000000;
          if (allowed) secure.setCACert(BACKEND_ROOT_CA);
        }
        const bool opened = allowed && (https ? http.begin(secure, url) : http.begin(plain, url));
        if (opened) {
          http.setConnectTimeout(2000);
          http.setTimeout(2000);
          http.addHeader("Authorization", String("Bearer ") + DEVICE_TOKEN);
          http.addHeader("Content-Type", "application/json");
          reply->status = job->kind == Config ? http.GET() : http.POST(String(job->body));
          if (reply->status == 200) {
            String body = http.getString();
            if (body.length() >= sizeof(reply->body)) reply->status = -3;
            else snprintf(reply->body, sizeof(reply->body), "%s", body.c_str());
          }
          http.end();
        } else reply->status = -2;
      }
      xQueueSend(replies_, reply, portMAX_DELAY);
    }
  }

 public:
  bool begin() {
    if (!ENABLE_NETWORK) return true;
    if (!strlen(BACKEND_URL) || !strlen(DEVICE_TOKEN)) return false;
    jobs_ = xQueueCreate(1, sizeof(Job));
    replies_ = xQueueCreate(1, sizeof(Reply));
    if (jobs_ && replies_ && xTaskCreate(worker, "mdp-http", 8192, this, 1, nullptr) == pdPASS) return true;
    if (jobs_) vQueueDelete(jobs_);
    if (replies_) vQueueDelete(replies_);
    jobs_ = replies_ = nullptr;
    return false;
  }

  void pump(mdp::Controller& controller, uint64_t now) {
    if (!ENABLE_NETWORK || !jobs_ || !replies_) return;
    static Reply reply; // Main task only; keep the 6KB buffer off its stack.
    if (xQueueReceive(replies_, &reply, 0) == pdTRUE) {
      inFlight_ = false;
      JsonDocument body;
      if (reply.status != 200 || deserializeJson(body, reply.body)) {
        Serial.printf("sync unavailable (status=%d); local controller continues\n", reply.status);
        retryAt_ = now + 2000;
      } else if (reply.kind == Config) {
        mdp::Text result = controller.applyConfig(body.as<JsonVariantConst>());
        JsonDocument ack;
        ack["revision"] = body["revision"];
        ack["status"] = result == "applied" || result == "unchanged" ? "applied" :
                        result == "deferred" ? "deferred" : "rejected";
        ack["reason"] = result;
        pendingAck_.clear(); serializeJson(ack, pendingAck_);
      } else if (reply.kind == Event) {
        if (body["accepted"] == true && body["event_id"].as<mdp::Text>() == reply.eventId) {
          if (!controller.store.acknowledge(reply.eventId)) controller.fail("storage_failed");
        } else retryAt_ = now + 2000;
      }
    }
    if (inFlight_ || now < retryAt_ || (controller.phase == mdp::Phase::Error && !controller.store.healthy))
      return;
    static Job job;
    job.body[0] = job.eventId[0] = 0;
    if (now >= nextConfig_) {
      job.kind = Config;
      nextConfig_ = now + 5000;
    } else if (!pendingAck_.empty()) {
      job.kind = ConfigAck;
      if (pendingAck_.size() >= sizeof(job.body)) return;
      snprintf(job.body, sizeof(job.body), "%s", pendingAck_.c_str());
      // Regenerated on the next successful config poll if this request fails.
      pendingAck_.clear();
    } else if (controller.store.data["pending"].size()) {
      job.kind = Event;
      JsonVariantConst event = controller.store.data["pending"][0];
      if (measureJson(event) >= sizeof(job.body)) { controller.fail("event_too_large"); return; }
      serializeJson(event, job.body, sizeof(job.body));
      snprintf(job.eventId, sizeof(job.eventId), "%s", event["event_id"].as<const char*>());
    } else return;
    inFlight_ = xQueueSend(jobs_, &job, 0) == pdTRUE;
  }
};
