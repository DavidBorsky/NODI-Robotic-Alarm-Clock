#include "../NODI/NodiCore.h"
#include <cassert>
#include <cstdio>
#include <cmath>
#include <limits>

using namespace nodi;
int main() {
    unsigned groups = 0;
    const uint32_t day = 20000, base = day * 86400u, seven = base + 7*3600;
    {
        // CAD's +X right-hand pitch lowers the -Y-facing head: sleep down, wake up.
        assert(desiredPose(State::Idle,0).pitch==8);
        assert(desiredPose(State::Snooze,0).pitch==20);
        assert(desiredPose(State::Prewake,0).pitch==-8);
        assert(desiredPose(State::Cheer,0).pitch==-12);
        for(uint32_t ms=0;ms<9600;ms+=20) {
            Pose p=desiredPose(State::Ringing,ms);
            assert(p.yaw>=-30 && p.yaw<=30 && p.pitch>=-15 && p.pitch<=25);
        }
        ++groups;
    }
    {
        Alarm a;
        assert(!a.configure(24, 0, true));
        assert(!a.configure(7, 60, true));
        a.update(seven-31, 0, true); assert(a.state()==State::Idle);
        a.update(seven-30, 20, true); assert(a.state()==State::Prewake);
        a.update(seven+17, 40, true); assert(a.state()==State::Ringing);
        assert(a.lastFiredDay()==day && a.takeOccurrenceChanged());
        assert(!a.takeOccurrenceChanged());
        assert(a.audible(40)); assert(!a.audible(600)); ++groups;
        a.update(seven+20, 1000, true, ButtonEvent::ShortPress);
        assert(a.state()==State::Snooze);
        a.update(seven+319, 300999, true); assert(a.state()==State::Snooze);
        a.update(seven+320, 301000, true); assert(a.state()==State::Ringing); ++groups;
        a.update(seven+321, 302000, true, ButtonEvent::LongPress);
        assert(a.state()==State::Cheer);
        a.update(seven+10, 306000, true); assert(a.state()==State::Idle);
        // Clock set back into today's alarm minute cannot retrigger.
        a.update(seven+1, 307000, true); assert(a.state()==State::Idle);
        a.update(seven+86400u, 308000, true); assert(a.state()==State::Ringing); ++groups;
    }
    {
        Alarm a; a.update(seven+61, 0, true); assert(a.state()==State::Idle);
        a.update(seven+86400u+59, 20, true); assert(a.state()==State::Ringing);
        a.update(seven+86400u+660, 600020, true); assert(a.state()==State::Cheer);
        a.update(seven+86400u+665, 604020, true); assert(a.state()==State::Idle); ++groups;
    }
    {
        Alarm a; a.configure(0, 0, true);
        a.update(base+86380u, 0, true); assert(a.state()==State::Prewake);
        a.update(base+86400u, 20, true); assert(a.state()==State::Ringing);
        a.update(base+86402u, 40, true, ButtonEvent::LongPress);
        a.update(base+86410u, 4040, true); assert(a.state()==State::Idle); ++groups;
    }
    {
        Alarm a; a.configure(23, 59, true);
        a.update(base+86340u, 0, true);
        a.update(base+86345u, 50, true, ButtonEvent::ShortPress);
        a.update(base+86645u, 300050, true); assert(a.state()==State::Ringing); ++groups;
    }
    {
        Alarm a; uint32_t nearWrap=0xFFFFFF00u;
        a.update(seven, nearWrap, true);
        a.update(seven+1, nearWrap+20u, true, ButtonEvent::ShortPress);
        a.update(seven+301, nearWrap+300020u, true); assert(a.state()==State::Ringing); ++groups;
        a.setEnabled(false); a.update(seven+302, 500, true); assert(a.state()==State::Idle);
        a.setEnabled(true); a.update(seven+303, 520, false); assert(a.state()==State::Idle); ++groups;
    }
    {
        Alarm a; a.restoreLastFiredDay(day); a.update(seven+3, 0, true);
        assert(a.state()==State::Idle); // reboot persistence
        a.update(seven+86400u, 1, true); assert(a.state()==State::Ringing); ++groups;
    }
    {
        Button b;
        assert(b.update(true,0)==ButtonEvent::None);
        b.update(false,5); b.update(true,10); // bounce
        assert(b.update(true,39)==ButtonEvent::None);
        b.update(true,40); b.update(false,100);
        assert(b.update(false,130)==ButtonEvent::ShortPress);
        b.update(true,200); b.update(true,230);
        assert(b.update(true,1730)==ButtonEvent::LongPress);
        assert(b.update(true,1800)==ButtonEvent::None);
        b.update(false,1810); assert(b.update(false,1840)==ButtonEvent::None); ++groups;
    }
    {
        Button b; uint32_t start=0xFFFFFF00u;
        b.update(true,start); b.update(true,start+30u);
        assert(b.update(true,start+1530u)==ButtonEvent::LongPress); ++groups;
    }
    {
        // Sampled trajectory derivatives independently check limits and exact endpoints.
        SmoothAxis a(-30,30); a.target(500);
        float p0=0, v0=0, maxV=0,maxA=0;
        for(uint32_t ms=0;ms<=5000;ms+=10) {
            float p=a.update(ms); assert(p>=-30.0001f && p<=30.0001f);
            float v=(p-p0)/0.01f;
            if(ms>10) maxA=fmaxf(maxA,fabsf((v-v0)/0.01f));
            maxV=fmaxf(maxV,fabsf(v)); p0=p;v0=v;
        }
        assert(fabsf(a.value()-30)<0.001f); assert(maxV<60.1f); assert(maxA<180.5f);
        std::printf("Measured sampled command limits: %.3f deg/s, %.3f deg/s^2 (10ms sampling).\n",maxV,maxA);
        a.target(-500); for(uint32_t ms=5001;ms<10000;++ms) a.update(ms);
        assert(fabsf(a.value()+30)<0.001f); ++groups;
        SmoothAxis b(-15,25); b.target(25); b.update(0); float at=b.update(250);
        b.target(-15); assert(fabsf(b.update(250)-at)<0.0001f);
        for(uint32_t ms=251;ms<5000;++ms) {
            float q=b.update(ms); assert(q>=-15.0001f && q<=25.0001f);
        }
        assert(fabsf(b.value()+15)<0.001f); ++groups;
        SmoothAxis c(-30,30); c.target(20); c.update(0xFFFFFF00u);
        c.update(0xFFFFFF00u+3000u); assert(fabsf(c.value()-20)<0.001f); ++groups;
    }
    std::printf("PASS: %u scenario groups (alarm, snooze, dismiss, midnight, timeout, reboot, clock invalid, debounce, millis rollover, bounded smooth motion).\n",groups);
    return 0;
}
