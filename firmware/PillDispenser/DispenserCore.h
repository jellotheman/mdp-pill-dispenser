#pragma once
// Portable application logic. ArduinoJson and AgileStateMachine are dependencies,
// installed by their package managers; their implementation is not copied here.
#include <ArduinoJson.h>
#include <AgileStateMachine.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>

namespace mdp {
constexpr unsigned CAPACITY = 6, MAX_PENDING = 24;
constexpr uint64_t AUTH_MS = 20000, HOLD_MS = 2000, VERIFY_MS = 8000;
constexpr const char* TIMEZONE = "Asia/Kolkata";
using Text = std::string;

inline bool identifier(const char* s) {
  if (!s || !*s || strlen(s) > 32) return false;
  for (; *s; ++s)
    if (!((*s >= 'a' && *s <= 'z') || (*s >= 'A' && *s <= 'Z') ||
          (*s >= '0' && *s <= '9') || *s == '-' || *s == '_')) return false;
  return true;
}

inline bool validConfig(JsonVariantConst c, Text& reason) {
  auto bad = [&](const char* why) { reason = why; return false; };
  if (!c.is<JsonObjectConst>() || c.size() != 3 || !c["revision"].is<uint32_t>() ||
      !c["timezone"].is<const char*>() || c["timezone"].as<Text>() != TIMEZONE ||
      !c["schedules"].is<JsonArrayConst>() || c["schedules"].size() > 32)
    return bad("invalid config envelope");
  JsonArrayConst rows = c["schedules"];
  for (size_t i = 0; i < rows.size(); ++i) {
    JsonVariantConst r = rows[i];
    const char* id = r["id"] | "";
    const char* time = r["time"] | "";
    if (!r.is<JsonObjectConst>() || r.size() != 5 || !identifier(id) ||
        strlen(time) != 5 || time[2] != ':' ||
        time[0] < '0' || time[0] > '2' || time[1] < '0' || time[1] > '9' ||
        time[3] < '0' || time[3] > '5' || time[4] < '0' || time[4] > '9' ||
        (time[0] == '2' && time[1] > '3') ||
        !r["compartment"].is<unsigned>() || r["compartment"].as<unsigned>() < 1 ||
        r["compartment"].as<unsigned>() > CAPACITY || !r["enabled"].is<bool>() ||
        !r["auth_user_id"].is<unsigned>() || r["auth_user_id"].as<unsigned>() < 1 ||
        r["auth_user_id"].as<unsigned>() > 1000)
      return bad("invalid schedule");
    for (size_t j = 0; j < i; ++j)
      if (rows[j]["id"].as<Text>() == id) return bad("duplicate schedule id");
  }
  return true;
}

struct Dose {
  Text id, schedule;
  unsigned compartment = 0, user = 0;
  uint32_t revision = 0;
};

struct Persistence {
  enum Load { Fresh, Loaded, Broken };
  virtual Load load(JsonDocument&) = 0;
  virtual bool save(const JsonDocument&) = 0;
  virtual ~Persistence() = default;
};

// The physical team must implement these operations for the selected mechanism.
// home/select may report an immediate completion for a mechanism that needs none.
struct Mechanism {
  virtual bool ready() const = 0;
  virtual bool simulated() const = 0;
  virtual bool home(uint64_t now) = 0;
  virtual bool select(unsigned compartment, uint64_t now) = 0;
  virtual bool release(const Dose&, uint64_t now) = 0;
  virtual bool finished(uint64_t now) = 0;
  virtual bool sensorClear() = 0;
  virtual void stop() = 0;
  virtual ~Mechanism() = default;
};

class Store {
 public:
  JsonDocument data;
  bool healthy = true;
  const Text device;
  Store(Persistence& port, const char* deviceId, const char* session)
      : device(deviceId), port_(port), session_(session) {}

  bool begin(bool simulation) {
    auto result = port_.load(data);
    if (result == Persistence::Broken) return healthy = false;
    if (result == Persistence::Fresh) {
      data.clear();
      data["version"] = 2;
      data["device_id"] = device;
      data["fault"] = nullptr;
      auto config = data["config"].to<JsonObject>();
      config["revision"] = 0;
      config["timezone"] = TIMEZONE;
      config["schedules"].to<JsonArray>();
      data["records"].to<JsonObject>();
      data["pending"].to<JsonArray>();
      auto slots = data["slots"].to<JsonObject>();
      for (unsigned n = 1; n <= CAPACITY; ++n)
        slots[std::to_string(n)] = simulation ? "loaded" : "unknown";
      return commit(data);
    }
    Text reason;
    if (!data.is<JsonObject>() || data.size() != 7 || data["version"] != 2 ||
        data["device_id"].as<Text>() != device ||
        !(data["fault"].isNull() || data["fault"].is<const char*>()) ||
        !validConfig(data["config"], reason) || !data["records"].is<JsonObject>() ||
        !data["slots"].is<JsonObject>() || data["slots"].size() != CAPACITY ||
        !data["pending"].is<JsonArray>() || data["pending"].size() > MAX_PENDING)
      return healthy = false;
    for (JsonPair p : data["records"].as<JsonObject>()) {
      Text status = p.value().as<Text>();
      if (status != "started" && status != "dispensed" && status != "missed" && status != "error")
        return healthy = false;
    }
    for (unsigned n = 1; n <= CAPACITY; ++n) {
      Text status = data["slots"][std::to_string(n)].as<Text>();
      if (status != "loaded" && status != "spent" && status != "quarantined" && status != "unknown")
        return healthy = false;
    }
    for (JsonVariant e : data["pending"].as<JsonArray>())
      if (!e["event_id"].is<const char*>() || e["device_id"].as<Text>() != device ||
          e["schema_version"] != 2) return healthy = false;
    return true;
  }

  JsonDocument event(const char* name, const char* state, uint64_t now,
                     const Dose& dose, const char* reason, unsigned count, bool simulated) {
    JsonDocument e;
    e["schema_version"] = 2;
    e["event_id"] = device + ":" + session_ + ":" + std::to_string(++sequence_);
    e["device_id"] = device;
    e["session_id"] = session_;
    e["event"] = name;
    e["state"] = state;
    e["elapsed_ms"] = now;
    e["occurred_at"] = nullptr; // No fabricated calendar time.
    if (dose.id.empty()) e["dose_id"] = nullptr; else e["dose_id"] = dose.id;
    if (dose.schedule.empty()) e["schedule_id"] = nullptr; else e["schedule_id"] = dose.schedule;
    e["compartment"] = dose.compartment;
    e["revision"] = dose.revision;
    e["reason"] = reason;
    e["observed_count"] = count;
    e["simulated"] = simulated;
    return e;
  }

  bool seen(const Dose& d) const { return !data["records"][d.id].isNull(); }
  bool loaded(const Dose& d) const {
    return data["slots"][std::to_string(d.compartment)].as<Text>() == "loaded";
  }
  bool recoveryNeeded() const {
    if (!data["fault"].isNull()) return true;
    for (JsonPairConst p : data["records"].as<JsonObjectConst>()) {
      Text s = p.value().as<Text>();
      if (s == "started" || s == "error") return true;
    }
    return false;
  }

  bool record(const Dose& d, const char* status, const JsonDocument& event) {
    if (!healthy || data["pending"].size() >= MAX_PENDING) return false;
    if (strcmp(status, "started") == 0 && (seen(d) || !loaded(d))) return false;
    JsonDocument next(data);
    next["records"][d.id] = status;
    if (strcmp(status, "started") == 0) next["slots"][std::to_string(d.compartment)] = "quarantined";
    if (strcmp(status, "dispensed") == 0) next["slots"][std::to_string(d.compartment)] = "spent";
    next["pending"].as<JsonArray>().add(event);
    return commit(next);
  }

  bool fault(const Dose& d, const char* reason, const JsonDocument& event) {
    if (!healthy) return false;
    JsonDocument next(data);
    next["fault"] = reason;
    if (!d.id.empty()) next["records"][d.id] = "error";
    if (next["pending"].size() < MAX_PENDING) next["pending"].as<JsonArray>().add(event);
    return commit(next); // Persist the lock even when the outbox is full.
  }

  bool configure(JsonVariantConst config) {
    JsonDocument next(data);
    next["config"].set(config);
    return commit(next);
  }

  bool enqueue(const JsonDocument& event) {
    if (!healthy || data["pending"].size() >= MAX_PENDING) return false;
    JsonDocument next(data);
    next["pending"].as<JsonArray>().add(event);
    return commit(next);
  }

  bool acknowledge(const Text& eventId) {
    JsonDocument next(data);
    JsonArray a = next["pending"].as<JsonArray>();
    for (size_t i = 0; i < a.size(); ++i)
      if (a[i]["event_id"].as<Text>() == eventId) { a.remove(i); return commit(next); }
    return true;
  }

 private:
  Persistence& port_;
  Text session_;
  uint32_t sequence_ = 0;
  bool commit(const JsonDocument& next) {
    if (!healthy || next.overflowed() || measureJson(next) > 12000 || !port_.save(next))
      return healthy = false;
    if (&next != &data) data.set(next);
    return true;
  }
};

enum class Phase { Idle, Waiting, Homing, Positioning, Releasing, Verifying, Completed, Missed, Error };
enum class Trigger { None, Due, Authorized, Expired, HomeDone, PositionDone, ReleaseDone, Verified, Settled, Fault };

class Controller {
 public:
  using Emit = void (*)(const JsonDocument&);
  Controller(Mechanism& mechanism, Store& store, Emit emit)
      : mechanism(mechanism), store(store), emit_(emit),
        states_{
          State("IDLE", &enter<Phase::Idle>), State("WAITING_FOR_FINGERPRINT", &enter<Phase::Waiting>),
          State("HOMING", &enter<Phase::Homing>), State("POSITIONING", &enter<Phase::Positioning>),
          State("RELEASING", &enter<Phase::Releasing>), State("VERIFYING", &enter<Phase::Verifying>),
          State("COMPLETED", &enter<Phase::Completed>), State("MISSED", &enter<Phase::Missed>),
          State("ERROR", &enter<Phase::Error>)} {
    for (auto& s : states_) fsm_.addState(s);
    link<Trigger::Due>(Phase::Idle, Phase::Waiting);
    link<Trigger::Expired>(Phase::Idle, Phase::Missed);
    link<Trigger::Authorized>(Phase::Waiting, Phase::Homing);
    link<Trigger::Expired>(Phase::Waiting, Phase::Missed);
    link<Trigger::HomeDone>(Phase::Homing, Phase::Positioning);
    link<Trigger::PositionDone>(Phase::Positioning, Phase::Releasing);
    link<Trigger::ReleaseDone>(Phase::Releasing, Phase::Verifying);
    link<Trigger::Verified>(Phase::Verifying, Phase::Completed);
    link<Trigger::Settled>(Phase::Completed, Phase::Idle);
    link<Trigger::Settled>(Phase::Missed, Phase::Idle);
    for (unsigned i = 0; i < 8; ++i) link<Trigger::Fault>(static_cast<Phase>(i), Phase::Error);
    fsm_.setInitialState(states_[0]);
    fsm_.start();
  }

  bool begin() {
    if (!store.healthy) fail("storage_requires_inspection");
    else if (store.recoveryNeeded()) fail("recovery_required");
    else if (!mechanism.ready()) fail("physical_mechanism_not_configured");
    return phase != Phase::Error;
  }

  const char* state() { return fsm_.getActiveStateName(); }
  bool idle() const { return phase == Phase::Idle; }
  Mechanism& mechanism;
  Store& store;
  Phase phase = Phase::Idle;
  uint64_t now = 0;
  Dose dose;
  unsigned count = 0;

  bool offer(const Dose& d, uint64_t at, int64_t remaining = AUTH_MS) {
    tick(at);
    if (!idle() || store.seen(d)) return false;
    if (d.id.empty() || !identifier(d.schedule.c_str()) || d.compartment < 1 ||
        d.compartment > CAPACITY || d.user < 1 || d.user > 1000) return false;
    dose = d; count = 0; deadline_ = at + (remaining > 0 ? remaining : 0);
    if (remaining <= 0) dispatch(Trigger::Expired);
    else if (!store.loaded(dose)) fail("compartment_requires_refill");
    else dispatch(Trigger::Due);
    return true;
  }

  bool authenticate(unsigned userId, uint64_t at) {
    tick(at);
    if (phase != Phase::Waiting) return false;
    if (userId != dose.user) { report("authentication_failed"); return false; }
    auto e = make("authorized");
    if (!store.record(dose, "started", e)) { fail("storage_failed"); return false; }
    emit_(e);
    dispatch(Trigger::Authorized);
    return phase != Phase::Error;
  }

  bool passage(uint64_t at) {
    tick(at); // A deadline wins over a late input.
    if (phase != Phase::Releasing && phase != Phase::Verifying) return false;
    if (++count > 1) fail("unexpected_extra_passage");
    else report("pill_detected");
    return true;
  }

  Text applyConfig(JsonVariantConst config) {
    Text reason;
    if (!validConfig(config, reason)) return "rejected:" + reason;
    uint32_t current = store.data["config"]["revision"];
    uint32_t revision = config["revision"];
    if (revision < current) return "rejected:stale revision";
    if (revision == current) {
      return store.data["config"].as<JsonVariantConst>() == config ?
             "unchanged" : "rejected:revision content changed";
    }
    if (!idle()) return "deferred";
    if (!store.configure(config)) { fail("storage_failed"); return "rejected:storage failed"; }
    return "applied";
  }

  void tick(uint64_t at) {
    if (at < now) { fail("monotonic_clock_reversed"); return; }
    now = at;
    uint64_t age = now - entered_;
    if (phase == Phase::Completed || phase == Phase::Missed) {
      if (age >= HOLD_MS) dispatch(Trigger::Settled);
    } else if (phase == Phase::Waiting) {
      if (now >= deadline_) dispatch(Trigger::Expired);
      else if (now - reminder_ >= 5000) { reminder_ = now; report("reminder"); }
    } else if (phase >= Phase::Homing && phase <= Phase::Verifying) {
      uint64_t limit = phase == Phase::Verifying ? VERIFY_MS : phase == Phase::Releasing ? 3000 : 5000;
      if (age >= limit) { fail("mechanism_or_verification_timeout"); return; }
      if (phase == Phase::Verifying) {
        // Allow a settling interval in which extra passages can be detected.
        if (age >= 500 && count == 1) dispatch(Trigger::Verified);
      } else if (mechanism.finished(now)) {
        dispatch(phase == Phase::Homing ? Trigger::HomeDone :
                 phase == Phase::Positioning ? Trigger::PositionDone : Trigger::ReleaseDone);
      }
    }
  }

  void fail(const char* reason) {
    if (phase == Phase::Error) return;
    faultReason_ = reason;
    dispatch(Trigger::Fault);
  }

 private:
  State states_[9];
  StateMachine fsm_;
  Emit emit_;
  Trigger trigger_ = Trigger::None;
  uint64_t deadline_ = 0, entered_ = 0, reminder_ = 0;
  const char* reason_ = nullptr;
  bool entryFailed_ = false;
  inline static Controller* active_ = nullptr; // Only the main control task dispatches.

  template<Trigger T> static bool condition() { return active_->trigger_ == T; }
  template<Phase P> static void enter() { active_->onEnter(P); }
  template<Trigger T> void link(Phase from, Phase to) {
    states_[static_cast<unsigned>(from)].addTransition(states_[static_cast<unsigned>(to)], &condition<T>);
  }

  void dispatch(Trigger t) {
    active_ = this; trigger_ = t;
    fsm_.execute();
    trigger_ = Trigger::None;
    // Do not recursively transition from a library entry callback.
    if (entryFailed_) { entryFailed_ = false; fail(reason_ ? reason_ : "stage_start_failed"); }
  }

  JsonDocument make(const char* name, const char* reason = nullptr) {
    return store.event(name, state(), now, dose, reason, count, mechanism.simulated());
  }
  void report(const char* name) { auto e = make(name); emit_(e); }

  void onEnter(Phase next) {
    phase = next; entered_ = now; reason_ = nullptr;
    bool ok = true;
    switch (next) {
      case Phase::Idle: dose = Dose{}; break;
      case Phase::Waiting: {
        reminder_ = now;
        auto e = make("dose_due");
        ok = store.enqueue(e);
        if (!ok) reason_ = "storage_failed";
        if (ok) { emit_(e); report("reminder"); }
        break;
      }
      case Phase::Homing: ok = mechanism.home(now); if (ok) report("homing"); break;
      case Phase::Positioning: ok = mechanism.select(dose.compartment, now); if (ok) report("positioning"); break;
      case Phase::Releasing:
        count = 0;
        if (!mechanism.sensorClear()) { reason_ = "sensor_obstructed_before_release"; ok = false; }
        else { ok = mechanism.release(dose, now); if (ok) report("releasing"); }
        break;
      case Phase::Verifying: report("verifying"); break;
      case Phase::Completed:
      case Phase::Missed: {
        const char* status = next == Phase::Completed ? "dispensed" : "missed";
        auto e = make(status, next == Phase::Completed ? "one_passage_observed" : "authentication_window_expired");
        ok = store.record(dose, status, e);
        if (ok) emit_(e);
        else reason_ = "storage_failed";
        break;
      }
      case Phase::Error: {
        mechanism.stop();
        // fail() assigned the reason before dispatch; preserve it through entry.
        auto e = make("error", faultReason_);
        store.fault(dose, faultReason_, e);
        emit_(e);
        break;
      }
    }
    if (!ok) entryFailed_ = true;
  }

  const char* faultReason_ = "controller_fault";
};

inline bool offerDaily(Controller& c, const char* date, unsigned secondsOfDay, uint64_t now) {
  if (!c.idle()) return false;
  for (JsonObjectConst row : c.store.data["config"]["schedules"].as<JsonArrayConst>()) {
    if (!row["enabled"].as<bool>()) continue;
    const char* clock = row["time"];
    unsigned due = ((clock[0]-'0')*10 + clock[1]-'0')*3600 +
                   ((clock[3]-'0')*10 + clock[4]-'0')*60;
    if (secondsOfDay < due) continue;
    Dose d{Text(date) + ":" + row["id"].as<Text>(), row["id"].as<Text>(),
           row["compartment"].as<unsigned>(), row["auth_user_id"].as<unsigned>(),
           c.store.data["config"]["revision"].as<uint32_t>()};
    if (c.offer(d, now, 120000 - int64_t(secondsOfDay - due)*1000)) return true;
  }
  return false;
}

// No physical construction is silently selected. The simulator alone implements
// the provisional one-preloaded-item-per-compartment model.
class Simulation : public Mechanism {
 public:
  bool obstruction = false, stuck = false;
  unsigned selected = 0, releaseCount = 0;
  bool ready() const override { return true; }
  bool simulated() const override { return true; }
  bool home(uint64_t at) override { stage_ = 0; started_ = at; return true; }
  bool select(unsigned compartment, uint64_t at) override {
    selected = compartment; stage_ = 1; started_ = at;
    return compartment >= 1 && compartment <= CAPACITY;
  }
  bool release(const Dose& d, uint64_t at) override {
    if (d.compartment != selected || !sensorClear()) return false;
    ++releaseCount; stage_ = 2; started_ = at; gate(true); return true;
  }
  bool finished(uint64_t at) override {
    const unsigned times[] = {200, 300, 700};
    if (stuck || at - started_ < times[stage_]) return false;
    if (stage_ == 2) gate(false);
    return true;
  }
  bool sensorClear() override { return !obstruction; }
  void stop() override { gate(false); }
 protected:
  virtual void gate(bool open) {}
 private:
  unsigned stage_ = 0;
  uint64_t started_ = 0;
};

class UnconfiguredMechanism : public Mechanism {
 public:
  bool ready() const override { return false; }
  bool simulated() const override { return false; }
  bool home(uint64_t) override { return false; }
  bool select(unsigned, uint64_t) override { return false; }
  bool release(const Dose&, uint64_t) override { return false; }
  bool finished(uint64_t) override { return false; }
  bool sensorClear() override { return false; }
  void stop() override {}
};
} // namespace mdp
