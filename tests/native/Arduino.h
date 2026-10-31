#pragma once
// Only the Arduino clock/types needed by the REAL AgileStateMachine library.
// No controller, JSON, storage, or mechanism logic is substituted here.
#include <cstdint>
#include <cstddef>
#include <cstdlib>
class __FlashStringHelper;
uint32_t millis();
