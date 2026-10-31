#include <iostream>
#include <stdexcept>
#include <vector>
#include "DispenserCore.h"

uint32_t millis() { return 0; } // Library time transitions are unused; core receives explicit time.
#define CHECK(x) do { if (!(x)) throw std::runtime_error(#x); } while (0)

using namespace mdp;
std::vector<Text> emitted;
void output(const JsonDocument& e) { Text line; serializeJson(e, line); emitted.push_back(line); }

struct Memory : Persistence {
  Text bytes;
  bool broken = false, failSave = false;
  Load load(JsonDocument& d) override {
    if (broken) return Broken;
    if (bytes.empty()) return Fresh;
    return deserializeJson(d, bytes) ? Broken : Loaded;
  }
  bool save(const JsonDocument& d) override {
    if (failSave) return false;
    bytes.clear(); serializeJson(d, bytes); return true;
  }
};

struct Fixture {
  Memory memory;
  Simulation mechanism;
  Store store{memory, "test-device", "session-a"};
  Controller c{mechanism, store, output};
  Fixture() { emitted.clear(); CHECK(store.begin(true)); CHECK(c.begin()); }
};

Dose dose(const char* name = "2026-10-31:morning", unsigned slot = 1) {
  return Dose{name, "morning", slot, 7, 1};
}
JsonDocument config(uint32_t revision = 1) {
  JsonDocument d;
  d["revision"] = revision; d["timezone"] = TIMEZONE;
  auto r = d["schedules"].to<JsonArray>().add<JsonObject>();
  r["id"] = "morning"; r["time"] = "08:00"; r["compartment"] = 2;
  r["enabled"] = true; r["auth_user_id"] = 7;
  return d;
}
void start(Fixture& f) { CHECK(f.c.offer(dose(), 0)); CHECK(f.c.authenticate(7, 100)); }
void releasing(Fixture& f) {
  start(f); f.c.tick(300); CHECK(f.c.phase == Phase::Positioning);
  f.c.tick(600); CHECK(f.c.phase == Phase::Releasing);
}
void complete(Fixture& f) {
  releasing(f); CHECK(f.c.passage(650)); f.c.tick(1300);
  CHECK(f.c.phase == Phase::Verifying); f.c.tick(1800);
  CHECK(f.c.phase == Phase::Completed);
}
template<class F> void run(const char* name, F fn, unsigned& count) {
  fn(); ++count; std::cout << "PASS " << name << "\n";
}
int main(int argc, char**) {
  unsigned count = 0;
  try {
    run("complete cycle carries compartment into mechanism", [] {
      Fixture f; complete(f);
      CHECK(f.mechanism.selected == 1); CHECK(f.mechanism.releaseCount == 1);
      CHECK(f.store.data["slots"]["1"] == "spent");
      CHECK(f.store.data["records"][dose().id] == "dispensed");
    }, count);
    run("failed identity cannot start", [] {
      Fixture f; f.c.offer(dose(), 0); CHECK(!f.c.authenticate(8, 1));
      CHECK(f.c.phase == Phase::Waiting); CHECK(f.mechanism.releaseCount == 0);
    }, count);
    run("approval outside window ignored", [] {
      Fixture f; CHECK(!f.c.authenticate(7, 0)); CHECK(f.mechanism.releaseCount == 0);
    }, count);
    run("exact deadline wins", [] {
      Fixture f; f.c.offer(dose(), 0); CHECK(!f.c.authenticate(7, AUTH_MS));
      CHECK(f.c.phase == Phase::Missed);
    }, count);
    run("invalid approval does not extend deadline", [] {
      Fixture f; f.c.offer(dose(), 0); f.c.authenticate(0, AUTH_MS-1);
      f.c.tick(AUTH_MS); CHECK(f.c.phase == Phase::Missed);
    }, count);
    run("repeated approval never duplicates release", [] {
      Fixture f; releasing(f); CHECK(!f.c.authenticate(7, 601));
      CHECK(f.mechanism.releaseCount == 1);
    }, count);
    run("busy controller does not accept another occurrence", [] {
      Fixture f; start(f); CHECK(!f.c.offer(dose("another",2), 101));
    }, count);
    run("expired occurrence never consumes stock", [] {
      Fixture f; f.c.offer(dose(), 0, -1);
      CHECK(f.c.phase == Phase::Missed); CHECK(f.store.data["slots"]["1"] == "loaded");
    }, count);
    run("duplicate occurrence blocked after completion", [] {
      Fixture f; complete(f); f.c.tick(3800);
      CHECK(!f.c.offer(dose(), 3800)); CHECK(f.mechanism.releaseCount == 1);
    }, count);
    run("used slot cannot silently refill tomorrow", [] {
      Fixture f; complete(f); f.c.tick(3800);
      CHECK(f.c.offer(dose("2026-11-01:morning"), 3800));
      CHECK(f.c.phase == Phase::Error); CHECK(f.mechanism.releaseCount == 1);
    }, count);
    run("different loaded slot is usable", [] {
      Fixture f; complete(f); f.c.tick(3800);
      CHECK(f.c.offer(dose("next",2), 3800)); CHECK(f.c.phase == Phase::Waiting);
    }, count);
    run("reboot preserves duplicate ledger and outbox", [] {
      Fixture f; complete(f); size_t queued = f.store.data["pending"].size();
      Store next(f.memory, "test-device", "session-b"); CHECK(next.begin(true));
      Simulation m; Controller c(m,next,output); CHECK(c.begin());
      CHECK(!c.offer(dose(),0)); CHECK(next.data["pending"].size() == queued);
    }, count);
    run("interrupted attempt locks on reboot", [] {
      Fixture f; start(f);
      Store next(f.memory,"test-device","session-b"); CHECK(next.begin(true));
      Simulation m; Controller c(m,next,output); CHECK(!c.begin());
      CHECK(c.phase == Phase::Error); CHECK(m.releaseCount == 0);
    }, count);
    run("corrupt storage prevents movement", [] {
      Memory m; m.bytes = "broken";
      Store s(m,"test-device","a"); CHECK(!s.begin(true));
      Simulation mechanism; Controller c(mechanism,s,output); CHECK(!c.begin());
      CHECK(mechanism.releaseCount == 0);
    }, count);
    run("storage failure before authorization prevents movement", [] {
      Fixture f; f.c.offer(dose(),0); f.memory.failSave = true;
      CHECK(!f.c.authenticate(7,1)); CHECK(f.c.phase == Phase::Error);
      CHECK(f.mechanism.releaseCount == 0);
    }, count);
    run("obstructed sensor prevents release", [] {
      Fixture f; start(f); f.c.tick(300); f.mechanism.obstruction = true; f.c.tick(600);
      CHECK(f.c.phase == Phase::Error); CHECK(f.mechanism.releaseCount == 0);
    }, count);
    run("early passage does not count", [] {
      Fixture f; start(f); CHECK(!f.c.passage(150)); CHECK(f.c.count == 0);
    }, count);
    run("release-time passage is retained", [] {
      Fixture f; releasing(f); f.c.passage(650); f.c.tick(1300); f.c.tick(1800);
      CHECK(f.c.phase == Phase::Completed);
    }, count);
    run("extra passage faults during settling", [] {
      Fixture f; releasing(f); f.c.passage(650); f.c.tick(1300); f.c.passage(1400);
      CHECK(f.c.phase == Phase::Error);
    }, count);
    run("missing passage faults without retry", [] {
      Fixture f; releasing(f); f.c.tick(1300); f.c.tick(9300);
      CHECK(f.c.phase == Phase::Error); CHECK(f.mechanism.releaseCount == 1);
      CHECK(!f.c.authenticate(7,9400));
    }, count);
    run("late passage loses to verification deadline", [] {
      Fixture f; releasing(f); f.c.tick(1300);
      CHECK(!f.c.passage(9300)); CHECK(f.c.phase == Phase::Error);
    }, count);
    run("jammed homing times out", [] {
      Fixture f; start(f); f.mechanism.stuck = true; f.c.tick(5100);
      CHECK(f.c.phase == Phase::Error); CHECK(f.mechanism.releaseCount == 0);
    }, count);
    run("physical profile refuses unconfigured hardware", [] {
      Memory m; Store s(m,"physical","a"); CHECK(s.begin(false));
      UnconfiguredMechanism mechanism; Controller c(mechanism,s,output);
      CHECK(!c.begin()); CHECK(c.phase == Phase::Error);
      CHECK(s.data["slots"]["1"] == "unknown");
    }, count);
    run("configuration persisted across reboot", [] {
      Fixture f; auto d = config(); CHECK(f.c.applyConfig(d.as<JsonVariantConst>()) == "applied");
      Store s(f.memory,"test-device","b"); CHECK(s.begin(true));
      CHECK(s.data["config"]["revision"] == 1);
    }, count);
    run("same revision is idempotent", [] {
      Fixture f; auto d = config(); f.c.applyConfig(d.as<JsonVariantConst>());
      CHECK(f.c.applyConfig(d.as<JsonVariantConst>()) == "unchanged");
    }, count);
    run("same revision changed content is rejected", [] {
      Fixture f; auto d = config(); f.c.applyConfig(d.as<JsonVariantConst>());
      d["schedules"][0]["time"] = "09:00";
      CHECK(f.c.applyConfig(d.as<JsonVariantConst>()).find("rejected:") == 0);
    }, count);
    run("stale revision rejected", [] {
      Fixture f; auto d = config(2); f.c.applyConfig(d.as<JsonVariantConst>());
      d["revision"] = 1; CHECK(f.c.applyConfig(d.as<JsonVariantConst>()).find("rejected:") == 0);
    }, count);
    run("configuration deferred during an attempt", [] {
      Fixture f; start(f); auto d = config();
      CHECK(f.c.applyConfig(d.as<JsonVariantConst>()) == "deferred");
      CHECK(f.store.data["config"]["revision"] == 0);
    }, count);
    for (unsigned which = 0; which < 8; ++which) {
      run("invalid configuration is rejected", [which] {
        Fixture f; auto d = config();
        if (which == 0) d["schedules"][0]["time"] = "24:00";
        if (which == 1) d["schedules"][0]["compartment"] = 0;
        if (which == 2) d["schedules"][0]["compartment"] = 7;
        if (which == 3) d["schedules"][0]["auth_user_id"] = 0;
        if (which == 4) d["schedules"][0]["enabled"] = "yes";
        if (which == 5) d["timezone"] = "UTC";
        if (which == 6) d["schedules"][0]["id"] = "bad:id";
        if (which == 7) d["schedules"].as<JsonArray>().add(d["schedules"][0]);
        CHECK(f.c.applyConfig(d.as<JsonVariantConst>()).find("rejected:") == 0);
      }, count);
    }
    run("scheduler produces a dated occurrence", [] {
      Fixture f; auto d=config(); f.c.applyConfig(d.as<JsonVariantConst>());
      CHECK(!offerDaily(f.c,"2026-10-31",28799,0));
      CHECK(offerDaily(f.c,"2026-10-31",28800,1000));
      CHECK(f.c.dose.id == "2026-10-31:morning"); CHECK(f.c.dose.compartment == 2);
    }, count);
    run("expired schedule records missed", [] {
      Fixture f; auto d=config(); f.c.applyConfig(d.as<JsonVariantConst>());
      CHECK(offerDaily(f.c,"2026-10-31",29000,0)); CHECK(f.c.phase == Phase::Missed);
    }, count);
    run("acknowledgement removes only the matching event", [] {
      Fixture f; complete(f);
      Text first=f.store.data["pending"][0]["event_id"].as<Text>();
      size_t n=f.store.data["pending"].size();
      CHECK(f.store.acknowledge("unrelated")); CHECK(f.store.data["pending"].size()==n);
      CHECK(f.store.acknowledge(first)); CHECK(f.store.data["pending"].size()==n-1);
    }, count);
    run("event id changes across sessions", [] {
      Fixture f; auto a=f.store.event("x","IDLE",0,Dose{},nullptr,0,true);
      Store s(f.memory,"test-device","session-b"); CHECK(s.begin(true));
      auto b=s.event("x","IDLE",0,Dose{},nullptr,0,true);
      CHECK(a["event_id"].as<Text>() != b["event_id"].as<Text>());
    }, count);
    run("full outbox locks before new movement and preserves pending events", [] {
      Fixture f;
      for (unsigned i=0;i<MAX_PENDING;++i) {
        auto e=f.store.event("x","IDLE",0,Dose{},nullptr,0,true); CHECK(f.store.enqueue(e));
      }
      f.c.offer(dose(),0); CHECK(f.c.phase==Phase::Error);
      CHECK(f.mechanism.releaseCount==0); CHECK(f.store.data["pending"].size()==MAX_PENDING);
      CHECK(!f.store.data["fault"].isNull());
    }, count);
    run("monotonic clock cannot move backwards", [] {
      Fixture f; f.c.tick(100); f.c.tick(99); CHECK(f.c.phase==Phase::Error);
    }, count);
    if (argc > 1) {
      Fixture f; complete(f);
      for (JsonVariantConst e : f.store.data["pending"].as<JsonArrayConst>()) {
        Text line; serializeJson(e,line); std::cout << "EVENT " << line << "\n";
      }
    }
    std::cout << "PASS " << count << " native firmware scenarios\n";
  } catch (const std::exception& e) {
    std::cerr << "FAIL after " << count << " scenarios: " << e.what() << "\n"; return 1;
  }
}
