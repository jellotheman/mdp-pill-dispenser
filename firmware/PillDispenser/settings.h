#pragma once
// SIMULATION_PROFILE is a capability choice, not a "finished hardware" switch.
// false deliberately blocks actuation until a real Mechanism is implemented.
constexpr bool SIMULATION_PROFILE = true;
constexpr bool DEMO_TIMERS = true;  // false uses daily schedules + DS1307.
constexpr bool ENABLE_NETWORK = false;
constexpr const char* DEVICE_ID = "mdp-demo";
constexpr const char* WIFI_SSID = "Wokwi-GUEST";
constexpr const char* WIFI_PASSWORD = "";
constexpr const char* BACKEND_URL = ""; // e.g. http://192.168.1.10:8000
constexpr const char* DEVICE_TOKEN = ""; // match MDP_DEVICE_TOKEN on the service
// For HTTPS, paste the issuing root CA PEM here. Certificate verification stays on.
// Time must also be valid: the network task requests NTP time after Wi-Fi connects.
constexpr const char* BACKEND_ROOT_CA = "";
