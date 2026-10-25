#pragma once
// Portable scheduling and trajectory core, shared by the Pico sketch and host tests.
// Wall time is local civil time encoded as UNIX seconds (no timezone/DST service).
#include <stdint.h>
#include <math.h>

namespace nodi {
enum class State { Idle, Prewake, Ringing, Snooze, Cheer };
enum class ButtonEvent { None, ShortPress, LongPress };

class Button {
    bool raw_ = false, stable_ = false, longSent_ = false;
    uint32_t changed_ = 0, pressed_ = 0;
public:
    ButtonEvent update(bool down, uint32_t ms) {
        if (down != raw_) { raw_ = down; changed_ = ms; }
        if (raw_ != stable_ && uint32_t(ms - changed_) >= 30) {
            stable_ = raw_;
            if (stable_) { pressed_ = ms; longSent_ = false; }
            else if (!longSent_) return ButtonEvent::ShortPress;
        }
        if (stable_ && !longSent_ && uint32_t(ms - pressed_) >= 1500) {
            longSent_ = true;
            return ButtonEvent::LongPress;
        }
        return ButtonEvent::None;
    }
};

class Alarm {
    uint16_t minute_ = 7 * 60;
    bool enabled_ = true;
    State state_ = State::Idle;
    uint32_t stateStart_ = 0;
    uint32_t lastFiredDay_ = 0xFFFFFFFFu;
    bool occurrenceChanged_ = false;
    void enter(State s, uint32_t ms) { state_ = s; stateStart_ = ms; }
public:
    bool configure(unsigned hour, unsigned minute, bool enabled) {
        if (hour > 23 || minute > 59) return false;
        minute_ = uint16_t(hour * 60 + minute);
        enabled_ = enabled;
        state_ = State::Idle;
        return true;
    }
    void setEnabled(bool on) { enabled_ = on; state_ = State::Idle; }
    bool enabled() const { return enabled_; }
    uint16_t alarmMinute() const { return minute_; }
    State state() const { return state_; }
    uint32_t lastFiredDay() const { return lastFiredDay_; }
    void restoreLastFiredDay(uint32_t day) { lastFiredDay_ = day; }
    bool takeOccurrenceChanged() {
        bool result = occurrenceChanged_; occurrenceChanged_ = false; return result;
    }
    void update(uint32_t wallSeconds, uint32_t ms, bool clockValid,
                ButtonEvent event = ButtonEvent::None) {
        if (!clockValid || !enabled_) { enter(State::Idle, ms); return; }
        if (event == ButtonEvent::LongPress &&
            (state_ == State::Ringing || state_ == State::Snooze)) enter(State::Cheer, ms);
        else if (event == ButtonEvent::ShortPress && state_ == State::Ringing)
            enter(State::Snooze, ms);

        // Monotonic durations survive wall-clock changes and uint32_t millis rollover.
        if (state_ == State::Snooze && uint32_t(ms - stateStart_) >= 300000u)
            enter(State::Ringing, ms);
        if (state_ == State::Ringing && uint32_t(ms - stateStart_) >= 600000u)
            enter(State::Cheer, ms); // 10-minute unattended timeout, consumed for today.
        if (state_ == State::Cheer && uint32_t(ms - stateStart_) >= 4000u)
            enter(State::Idle, ms);

        if (state_ == State::Ringing || state_ == State::Snooze || state_ == State::Cheer)
            return;
        const uint32_t day = wallSeconds / 86400u;
        const uint32_t todayAlarm = day * 86400u + uint32_t(minute_) * 60u;
        // Alarm remains eligible throughout its minute; no dependence on hitting second 0.
        // Deliberately do not replay alarms missed by more than one minute or loss of power.
        if (day != lastFiredDay_ && wallSeconds >= todayAlarm &&
            wallSeconds - todayAlarm < 60u) {
            lastFiredDay_ = day;
            occurrenceChanged_ = true;
            enter(State::Ringing, ms);
            return;
        }
        uint32_t nextAlarm = todayAlarm;
        if (wallSeconds >= todayAlarm || day == lastFiredDay_) nextAlarm += 86400u;
        if (nextAlarm > wallSeconds && nextAlarm - wallSeconds <= 30u)
            state_ = State::Prewake;
        else state_ = State::Idle;
    }
    bool audible(uint32_t ms) const {
        return state_ == State::Ringing && uint32_t(ms - stateStart_) % 1000u < 400u;
    }
};

struct Pose { float yaw, pitch; };
inline Pose desiredPose(State state, uint32_t ms) {
    // CAD right-hand rotation about +X: face points -Y, so positive pitch lowers face.
    switch (state) {
        case State::Prewake: return {0, -8};
        case State::Ringing: {
            // Slow alternating movements: enough time for each rest-to-rest trajectory.
            const unsigned phase = (ms / 2400u) % 4u;
            const float yaw[] = {-20, 0, 20, 0};
            const float pitch[] = {-8, -12, -8, 0};
            return {yaw[phase], pitch[phase]};
        }
        case State::Snooze: return {0, 20};
        case State::Cheer: return {0, -12};
        default: return {0, 8};
    }
}

class SmoothAxis {
    float lo_, hi_, value_, from_, to_, requested_;
    uint32_t began_ = 0;
    float durationMs_ = 0;
    bool moving_ = false;
    void start(uint32_t ms) {
        from_ = value_; to_ = requested_;
        const float distance = fabsf(to_ - from_);
        if (distance < 0.001f) { value_ = to_; moving_ = false; return; }
        // Quintic q=10u^3-15u^4+6u^5: max |q'|=1.875, max |q''|=5.773503.
        // T enforces <=60deg/s and <=180deg/s^2; minimum 0.5s.
        float seconds = fmaxf(0.5f, fmaxf(1.875f * distance / 60.0f,
                                         sqrtf(5.773503f * distance / 180.0f)));
        durationMs_ = seconds * 1000.0f;
        began_ = ms; moving_ = true;
    }
public:
    SmoothAxis(float low, float high, float initial = 0)
        : lo_(low), hi_(high), value_(initial), from_(initial), to_(initial),
          requested_(initial) {}
    void target(float angle) { requested_ = fminf(hi_, fmaxf(lo_, angle)); }
    float update(uint32_t ms) {
        if (!moving_) start(ms);
        if (!moving_) return value_;
        float u = float(uint32_t(ms - began_)) / durationMs_;
        if (u >= 1.0f) {
            value_ = to_; moving_ = false;
            // New request waits for this segment to finish, preserving zero endpoint speed.
            return value_;
        }
        const float u2 = u * u, u3 = u2 * u;
        value_ = from_ + (to_ - from_) * (10*u3 - 15*u3*u + 6*u3*u2);
        return value_;
    }
    float value() const { return value_; }
    bool moving() const { return moving_; }
};
} // namespace nodi
