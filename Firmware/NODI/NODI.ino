// NODI proof-of-concept hardware integration. Hardware has NOT been tested.
// Board: original Raspberry Pi Pico, Earle Philhower Arduino-Pico core.
#include <Arduino.h>
#include <Wire.h>
#include <Servo.h>
#include <EEPROM.h>
#include <RTClib.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <stddef.h>
#include "NodiCore.h"

constexpr uint8_t SDA_PIN=4, SCL_PIN=5, YAW_PIN=2, PITCH_PIN=3;
constexpr uint8_t BUTTON_PIN=15, PIEZO_PIN=16;
// Start with horns DISCONNECTED. Center, install horns at mechanical zero, then
// measure actual angle per pulse. These nominal values are commissioning assumptions.
constexpr float YAW_US_PER_DEG=1000.0f/180.0f, PITCH_US_PER_DEG=1000.0f/180.0f;
constexpr int YAW_CENTER_US=1500, PITCH_CENTER_US=1500;
// Pitch servo case moves against its fixed horn, reversing the shaft/head relation.
// These nominal polarities must still be verified on the actual servo installation.
constexpr int YAW_SIGN=1, PITCH_SIGN=-1;

nodi::Alarm alarm;
nodi::Button button;
nodi::SmoothAxis yaw(-30,30), pitch(-15,25);
Servo yawServo, pitchServo;
RTC_DS3231 rtc;
Adafruit_SSD1306 display(128,64,&Wire,-1);
bool rtcPresent=false, clockValid=false, displayPresent=false;
uint32_t wallSeconds=0, lastClockRead=0, lastFrame=0, lastDraw=0;

struct Settings {
    uint32_t magic;
    uint32_t lastFiredDay;
    uint8_t hour, minute, enabled, revision;
    uint32_t checksum;
};
static_assert(sizeof(Settings)==16,"settings layout changed");
Settings settings{};
uint32_t checksum(const Settings& s) {
    const auto* bytes=reinterpret_cast<const uint8_t*>(&s);
    uint32_t h=2166136261u;
    for(size_t i=0;i<offsetof(Settings,checksum);++i) h=(h^bytes[i])*16777619u;
    return h;
}
void persist() {
    settings.magic=0x4e4f4449u;
    settings.lastFiredDay=alarm.lastFiredDay();
    settings.hour=alarm.alarmMinute()/60;
    settings.minute=alarm.alarmMinute()%60;
    settings.enabled=alarm.enabled(); settings.revision=1;
    settings.checksum=checksum(settings);
    EEPROM.put(0,settings);
    if(!EEPROM.commit()) Serial.println("ERROR flash save failed; reboot duplicate protection unavailable");
}
void readClock() {
    // A failed bus acknowledgement suppresses the alarm instead of inventing time.
    Wire.beginTransmission(0x68);
    bool responding=Wire.endTransmission()==0;
    if(!responding) { clockValid=false; return; }
    if(!rtcPresent) rtcPresent=rtc.begin(&Wire);
    if(!rtcPresent) { clockValid=false; return; }
    DateTime t=rtc.now();
    clockValid=t.isValid() && t.year()>=2000 && t.year()<=2099 && !rtc.lostPower();
    if(clockValid) wallSeconds=t.unixtime();
}
bool i2cPresent(uint8_t address) {
    Wire.beginTransmission(address); return Wire.endTransmission()==0;
}
void status() {
    char line[80];
    snprintf(line,sizeof(line),"alarm %02u:%02u %s; clock %s; last fired day %lu",
        unsigned(alarm.alarmMinute()/60),unsigned(alarm.alarmMinute()%60),
        alarm.enabled()?"ON":"OFF",clockValid?"valid":"SET TIME REQUIRED",
        static_cast<unsigned long>(alarm.lastFiredDay()));
    Serial.println(line);
}
void command(const char* line) {
    unsigned y,m,d,h,n,s; char extra;
    if(sscanf(line,"TIME %u-%u-%u %u:%u:%u %c",&y,&m,&d,&h,&n,&s,&extra)==6 &&
       y>=2000 && y<=2099 && m>=1 && m<=12 && d>=1 && d<=31 && h<24 && n<60 && s<60) {
        DateTime t(y,m,d,h,n,s);
        if(t.isValid() && rtcPresent) {
            rtc.adjust(t); readClock(); Serial.println("Time set (local civil time, manual DST)");
            return;
        }
    }
    if(sscanf(line,"ALARM %u:%u %c",&h,&n,&extra)==2 && alarm.configure(h,n,alarm.enabled())) {
        persist(); status(); return;
    }
    if(strcmp(line,"ON")==0 || strcmp(line,"OFF")==0) {
        alarm.setEnabled(strcmp(line,"ON")==0); persist(); status(); return;
    }
    if(strcmp(line,"STATUS")==0) { status(); return; }
    Serial.println("Commands: TIME YYYY-MM-DD HH:MM:SS | ALARM HH:MM | ON | OFF | STATUS");
}
void serialInput() {
    static char line[64]; static size_t used=0; static bool overflow=false;
    // Bound serial work per loop so a continuously transmitting host cannot starve control.
    unsigned budget=64;
    while(Serial.available() && budget--) {
        char c=char(Serial.read());
        if(c=='\r') continue;
        if(c=='\n') {
            if(!overflow) { line[used]='\0'; command(line); }
            else Serial.println("ERROR command too long");
            used=0; overflow=false;
        } else if(used+1<sizeof(line) && !overflow) line[used++]=c;
        else overflow=true;
    }
}
void drawFace() {
    if(!displayPresent) return;
    display.clearDisplay(); display.setTextColor(SSD1306_WHITE);
    display.setTextSize(2); display.setCursor(32,0);
    if(clockValid) {
        DateTime t(wallSeconds); char timeText[8];
        snprintf(timeText,sizeof(timeText),"%02u:%02u",unsigned(t.hour()),unsigned(t.minute()));
        display.print(timeText);
    } else display.print("--:--");
    const nodi::State state=alarm.state();
    const bool sleepy=state==nodi::State::Idle || state==nodi::State::Snooze;
    if(sleepy) { display.drawLine(25,35,49,35,WHITE); display.drawLine(79,35,103,35,WHITE); }
    else if(state==nodi::State::Cheer) {
        display.drawLine(25,37,37,27,WHITE); display.drawLine(37,27,49,37,WHITE);
        display.drawLine(79,37,91,27,WHITE); display.drawLine(91,27,103,37,WHITE);
    } else { display.fillRoundRect(29,24,17,22,5,WHITE); display.fillRoundRect(82,24,17,22,5,WHITE); }
    display.setTextSize(1); display.setCursor(6,55);
    if(!clockValid) display.print("SET TIME VIA USB");
    else if(state==nodi::State::Ringing) display.print("Tap snooze; hold off");
    else if(state==nodi::State::Snooze) display.print("Snoozed 5m; hold off");
    else {
        char a[20]; snprintf(a,sizeof(a),"%s %02u:%02u",alarm.enabled()?"ALARM":"OFF",
            unsigned(alarm.alarmMinute()/60),unsigned(alarm.alarmMinute()%60)); display.print(a);
    }
    display.display();
}
int pulseFor(float degrees,int center,int sign,float scale) {
    return constrain(int(lroundf(center+sign*degrees*scale)),1000,2000);
}
void setup() {
    pinMode(BUTTON_PIN,INPUT_PULLUP); pinMode(PIEZO_PIN,OUTPUT); digitalWrite(PIEZO_PIN,LOW);
    Serial.begin(115200); // no wait for USB: the clock must start without a computer
    Wire.setSDA(SDA_PIN); Wire.setSCL(SCL_PIN); Wire.begin(); Wire.setClock(100000);
    EEPROM.begin(256); EEPROM.get(0,settings);
    if(settings.magic==0x4e4f4449u && settings.revision==1 &&
       settings.checksum==checksum(settings) && settings.hour<24 && settings.minute<60 && settings.enabled<=1) {
        alarm.configure(settings.hour,settings.minute,settings.enabled);
        alarm.restoreLastFiredDay(settings.lastFiredDay);
    } // corrupt/uninitialized settings use 07:00 ON, but invalid RTC still inhibits ringing
    rtcPresent=rtc.begin(&Wire); readClock();
    if(i2cPresent(0x3D)) displayPresent=display.begin(SSD1306_SWITCHCAPVCC,0x3D);
    else if(i2cPresent(0x3C)) displayPresent=display.begin(SSD1306_SWITCHCAPVCC,0x3C);
    if(displayPresent) {
        display.ssd1306_command(SSD1306_SETCONTRAST); display.ssd1306_command(32);
    }
    // Nominal servo range never used as an angle API: explicit microseconds only.
    yawServo.attach(YAW_PIN,1000,2000); pitchServo.attach(PITCH_PIN,1000,2000);
    yawServo.writeMicroseconds(YAW_CENTER_US); pitchServo.writeMicroseconds(PITCH_CENTER_US);
    lastClockRead=millis(); status();
}
void loop() {
    uint32_t ms=millis();
    serialInput();
    if(uint32_t(ms-lastClockRead)>=250) { lastClockRead=ms; readClock(); }
    nodi::ButtonEvent event=button.update(digitalRead(BUTTON_PIN)==LOW,ms);
    if(event==nodi::ButtonEvent::LongPress &&
       alarm.state()!=nodi::State::Ringing && alarm.state()!=nodi::State::Snooze) {
        alarm.setEnabled(!alarm.enabled()); persist(); event=nodi::ButtonEvent::None;
    }
    alarm.update(wallSeconds,ms,clockValid,event);
    // Store consumption before sounding so a normal reboot cannot re-ring the same day.
    if(alarm.takeOccurrenceChanged()) persist();
    if(uint32_t(ms-lastFrame)>=20) {
        lastFrame=ms; nodi::Pose pose=nodi::desiredPose(alarm.state(),ms);
        yaw.target(pose.yaw); pitch.target(pose.pitch);
        yawServo.writeMicroseconds(pulseFor(yaw.update(ms),YAW_CENTER_US,YAW_SIGN,YAW_US_PER_DEG));
        pitchServo.writeMicroseconds(pulseFor(pitch.update(ms),PITCH_CENTER_US,PITCH_SIGN,PITCH_US_PER_DEG));
        if(alarm.audible(ms)) tone(PIEZO_PIN,4000); else noTone(PIEZO_PIN);
    }
    if(uint32_t(ms-lastDraw)>=200) { lastDraw=ms; drawFace(); }
}
