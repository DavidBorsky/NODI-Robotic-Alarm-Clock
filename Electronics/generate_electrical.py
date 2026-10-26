#!/usr/bin/env python3
"""Generate NODI Rev B's editable KiCad hierarchy and explicit connection data.

Symbols are authored here and embedded, with a matching project symbol library.
KiCad CLI, not this script, performs parsing, ERC, PDF and XML-netlist export.
The model is a complete SYSTEM schematic using purchased module interfaces;
vendor PCB/IC internals are documented by primary-source links, not redesigned.
"""
import csv
import html
import json
from pathlib import Path
import uuid

HERE = Path(__file__).resolve().parent
SCHEM = HERE / "Schematics"
WIRING = HERE / "Wiring"
PROJECT = "NODI_System_RevB"
NAMESPACE = uuid.UUID("ab054a40-2901-4b62-8aee-9626a03a05ca")
LIB = {}
COMPONENTS = []
PINS = []

def uid(key): return str(uuid.uuid5(NAMESPACE, str(key)))
def q(value): return json.dumps(str(value), ensure_ascii=False)
def num(value): return f"{value:.5f}".rstrip("0").rstrip(".")
def effects(size=1.27, justify="", hide=False):
    return f'(effects (font (size {size} {size}))'+(f' (justify {justify})' if justify else '')+(' (hide yes)' if hide else '')+')'
def prop(key,value,x,y,hide=False,size=1.27):
    return f'(property {q(key)} {q(value)} (at {num(x)} {num(y)} 0) {effects(size,"",hide)})'
def line(points,width=.254,fill="none"):
    return '(polyline (pts '+" ".join(f'(xy {num(x)} {num(y)})' for x,y in points)+f') (stroke (width {width}) (type default)) (fill (type {fill})))'
def rectangle(x1,y1,x2,y2):
    return f'(rectangle (start {num(x1)} {num(y1)}) (end {num(x2)} {num(y2)} ) (stroke (width 0.254) (type default)) (fill (type background)))'
def pin(number,name,x,dy,angle,kind="passive"):
    return dict(number=str(number),name=name,x=x,dy=dy,angle=angle,kind=kind)
def box_symbol(name,left,right,width=50,step=5.08,height=None):
    # local dy follows the sheet's downward Y; KiCad library Y points upward.
    h=height or (max(len(left),len(right))-1)*step+12.7
    pins=[]
    for side,entries in [(-1,left),(1,right)]:
        for i,entry in enumerate(entries):
            number,label,*kind=entry
            dy=(i-(len(entries)-1)/2)*step
            pins.append(pin(number,label,side*(width/2+5.08),dy,0 if side<0 else 180,kind[0] if kind else "passive"))
    LIB[name]=dict(pins=pins,graphics=[rectangle(-width/2,h/2,width/2,-h/2)],width=width,height=h)
    return name

def basic_symbols():
    hp=[pin(1,"1",-7.62,0,0),pin(2,"2",7.62,0,180)]
    vp=[pin(1,"1",0,-7.62,270),pin(2,"2",0,7.62,90)]
    LIB["R_H"]=dict(pins=hp,graphics=[rectangle(-3.81,1.27,3.81,-1.27)],width=8,height=4)
    LIB["R_V"]=dict(pins=vp,graphics=[rectangle(-1.27,3.81,1.27,-3.81)],width=4,height=8)
    LIB["Fuse"]=dict(pins=hp,graphics=[rectangle(-3.81,1.27,3.81,-1.27),line([(-3.81,0),(3.81,0)])],width=8,height=4)
    LIB["Cap"]=dict(pins=vp,graphics=[line([(-3.81,1.27),(3.81,1.27)]),line([(-3.81,-1.27),(3.81,-1.27)]),line([(0,3.81),(0,1.27)]),line([(0,-1.27),(0,-3.81)])],width=8,height=8)
    LIB["Cap_Polar"]=dict(pins=[pin(1,"+",0,-7.62,270),pin(2,"-",0,7.62,90)],graphics=LIB["Cap"]["graphics"]+[line([(-5.08,3.81),(-2.54,3.81)]),line([(-3.81,2.54),(-3.81,5.08)])],width=8,height=8)
    LIB["Schottky"]=dict(pins=[pin(2,"A",-7.62,0,0),pin(1,"K",7.62,0,180)],graphics=[line([(-2.54,2.54),(-2.54,-2.54),(2.54,0),(-2.54,2.54)]),line([(2.54,-3.81),(2.54,3.81)]),line([(2.54,3.81),(1.27,3.81)]),line([(2.54,-3.81),(3.81,-3.81)])],width=8,height=8)
    LIB["NPN"]=dict(pins=[pin(2,"B",-7.62,0,0),pin(3,"C",5.08,-7.62,270),pin(1,"E",5.08,7.62,90)],graphics=[line([(-1.27,-3.81),(-1.27,3.81)]),line([(-2.54,0),(-1.27,0)]),line([(-1.27,1.27),(5.08,5.08)]),line([(-1.27,-1.27),(5.08,-5.08)]),line([(2.54,-3.81),(4.65,-4.65),(3.81,-2.54),(2.54,-3.81)],fill="outline")],width=10,height=12)
    LIB["Piezo"]=dict(pins=[pin(1,"+",0,-7.62,270),pin(2,"-",0,7.62,90)],graphics=[line([(-2.54,2.54),(-2.54,-2.54)]),line([(-1.27,2.54),(-1.27,-2.54)]),line([(-1.27,2.54),(3.81,5.08),(3.81,-5.08),(-1.27,-2.54)]),line([(0,3.81),(0,2.54)]),line([(0,-2.54),(0,-3.81)])],width=10,height=10)
    LIB["Testpoint"]=dict(pins=[pin(1,"",0,0,90)],graphics=[f'(circle (center 0 1.27) (radius 1.27) (stroke (width 0.254) (type default)) (fill (type none)))'],width=3,height=3)
    LIB["Flag"]=dict(pins=[pin(1,"",0,0,90,"power_out")],graphics=[line([(0,0),(0,2.54),(-2.54,3.81),(0,5.08),(2.54,3.81),(0,2.54)])],width=5,height=5)
    # These four project pin IDs identify two internally common terminal pairs.
    LIB["Tactile4"]=dict(pins=[pin("A1","A1",-10.16,-2.54,0),pin("A2","A2",-10.16,2.54,0),pin("B1","B1",10.16,-2.54,180),pin("B2","B2",10.16,2.54,180)],graphics=[line([(-5.08,2.54),(-5.08,-2.54)]),line([(5.08,2.54),(5.08,-2.54)]),line([(-5.08,0),(3.81,3.81)]),line([(0,3.81),(0,6.35)]),line([(-2.54,6.35),(2.54,6.35)])],width=12,height=12)

def library_definition(name, qualified=True):
    obj=LIB[name]; ident="NODI:"+name if qualified else name
    text=[f'(symbol {q(ident)} (pin_names (offset 0.762)) (in_bom yes) (on_board yes)',prop("Reference","U",0,0,True),prop("Value",name,0,0,True),f'(symbol {q(name+"_0_1")} '+" ".join(obj["graphics"])+')',f'(symbol {q(name+"_1_1")}']
    for p in obj["pins"]:
        # Passive pin segment is long enough to reach a module rectangle or device body.
        length=5.08 if len(obj["pins"])>4 else 3.81
        if name in ["Flag","Testpoint"]:length=0
        text.append(f'(pin {p["kind"]} line (at {num(p["x"])} {num(-p["dy"])} {p["angle"]}) (length {length}) (name {q(p["name"])} {effects(1.15)}) (number {q(p["number"])} {effects(1.05)}))')
    return "\n".join(text)+'))'

class Sheet:
    def __init__(self,name,title,page):
        self.name=name;self.title=title;self.page=page;self.parts=[];self.items=[];self.used=set();self.serial=0
        self.uuid=uid(name);self.path='/'+uid(PROJECT) if page==1 else '/'+uid(PROJECT)+'/'+uid('hierarchy/'+name)
    def key(self):self.serial+=1;return self.name+'/'+str(self.serial)
    def text(self,text,x,y,size=1.52):
        self.items.append(f'(text {q(text)} (at {num(x)} {num(y)} 0) {effects(size,"left")} (uuid {q(uid(self.key()))}))')
    def wire(self,a,b):
        self.items.append(f'(wire (pts (xy {num(a[0])} {num(a[1])}) (xy {num(b[0])} {num(b[1])})) (stroke (width 0) (type default)) (uuid {q(uid(self.key()))}))')
    def label(self,net,x,y,angle=0):
        self.items.append(f'(global_label {q(net)} (shape passive) (at {num(x)} {num(y)} {angle}) {effects(1.15,"right" if angle==180 else "left")} (uuid {q(uid(self.key()))}) '+prop('Intersheetrefs','${INTERSHEET_REFS}',x,y,True)+')')
    def junction(self,x,y):
        self.items.append(f'(junction (at {num(x)} {num(y)}) (diameter 0) (color 0 0 0 0) (uuid {q(uid(self.key()))}))')
    def outline(self,x,y,w,h):
        self.items.append('(polyline (pts '+" ".join(f'(xy {num(a)} {num(b)})' for a,b in [(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)])+f') (stroke (width 0.254) (type dash)) (uuid {q(uid(self.key()))}))')
    def add(self,ref,kind,value,x,y,nets,notes="",bom=True,wired=()):
        self.used.add(kind);obj=LIB[kind];pos={};sid=uid(ref)
        if kind in ['R_H','Fuse','Schottky']:
            props=prop('Reference',ref,x,y-7.62)+prop('Value',value,x,y-5.08)
        elif kind in ['R_V','Cap','Cap_Polar','Piezo']:
            props=prop('Reference',ref,x+10.16,y-2.54)+prop('Value',value,x+13.97,y+1.27)
        else:props=prop('Reference',ref,x,y-obj['height']/2-6.35)+prop('Value',value,x,y-obj['height']/2-3.81)
        if kind=='Flag':props=prop('Reference',ref,x,y,True)+prop('Value','PWR_FLAG',x,y,True)
        part=f'(symbol (lib_id {q("NODI:"+kind)}) (at {num(x)} {num(y)} 0) (unit 1) (in_bom {"yes" if bom else "no"}) (on_board no) (dnp no) (uuid {q(sid)}) '+props+prop('Footprint','',x,y,True)+prop('Description',notes,x,y,True)
        for p in obj['pins']:part+=f'(pin {q(p["number"])} (uuid {q(uid(ref+"/"+p["number"]))}))'
        part+=f'(instances (project {q(PROJECT)} (path {q(self.path)} (reference {q(ref)}) (unit 1)))))'
        self.parts.append(part)
        COMPONENTS.append(dict(ref=ref,value=value,symbol=kind,sheet=self.name,notes=notes,in_bom=bom))
        for p in obj['pins']:
            n=p['number'];a=(x+p['x'],y+p['dy']);pos[n]=a;net=nets.get(n)
            PINS.append(dict(reference=ref,pin=n,pin_name=p['name'],net=net or 'NC',electrical_type=p['kind'],sheet=self.name,notes=notes))
            if not net:
                self.items.append(f'(no_connect (at {num(a[0])} {num(a[1])}) (uuid {q(uid(ref+"/NC/"+n))}))')
            elif n not in [str(a) for a in wired]:
                if p['x']<0:b=(a[0]-5.08,a[1]);angle=180
                elif p['x']>0:b=(a[0]+5.08,a[1]);angle=0
                elif p['dy']<0:b=(a[0],a[1]-5.08);angle=0
                else:b=(a[0],a[1]+5.08);angle=0
                if kind in ['Flag','Testpoint']:b=(a[0],a[1]+5.08);angle=0
                self.wire(a,b);self.label(net,*b,angle)
        return pos
    def child(self,name,title,page,x,y):
        su=uid('hierarchy/'+name)
        self.items.append(f'(sheet (at {x} {y}) (size 140 25.4) (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {q(su)}) '+prop('Sheetname',title,x,y-2.54)+prop('Sheetfile',name+'.kicad_sch',x,y+28)+f'(instances (project {q(PROJECT)} (path {q("/"+uid(PROJECT))} (page {q(page)})))))')
    def write(self):
        title=f'(title_block (title {q(self.title)}) (date "2026-10-25") (rev "B") (company "NODI - David Borsky") (comment 1 "SYSTEM SCHEMATIC / PROTOTYPE / HARDWARE UNTESTED") (comment 2 "All module external pins shown; vendor PCB internals referenced separately"))'
        text=f'(kicad_sch (version 20250114) (generator "nodi-electrical-generator") (uuid {q(self.uuid if self.page!=1 else uid(PROJECT))}) (paper "A3") '+title+' (lib_symbols '+"\n".join(library_definition(k) for k in sorted(self.used))+')\n'+"\n".join(self.items+self.parts)
        if self.page==1:text+='(sheet_instances (path "/" (page "1")))'
        text+=')\n';(SCHEM/(self.name+'.kicad_sch')).write_text(text)

def build():
    basic_symbols()
    left=[(str(i),n,'power_in' if i==3 else 'output' if i in [4,5] else 'bidirectional' if i in [6,7] else 'input' if i==20 else 'passive' if n=='GND' else 'bidirectional') for i,n in enumerate(['GP0','GP1','GND','GP2','GP3','GP4','GP5','GND','GP6','GP7','GP8','GP9','GND','GP10','GP11','GP12','GP13','GND','GP14','GP15'],1)]
    right=[]
    names=['VBUS','VSYS','GND','3V3_EN','3V3_OUT','ADC_VREF','GP28_ADC2','AGND','GP27_ADC1','GP26_ADC0','RUN','GP22','GND','GP21','GP20','GP19','GP18','GND','GP17','GP16']
    for i,n in zip(range(40,20,-1),names):right.append((str(i),n,'power_in' if i==39 else 'power_out' if i==36 else 'output' if i==21 else 'passive' if i in [40,38,37,35,33,30,28,23] else 'bidirectional'))
    box_symbol('Pico',left,right,63.5,5.08,110)
    # Three SWD debug pads are exposed separately; header numbering remains 1..40.
    LIB['Pico']['pins'] += [pin('SWCLK','SWCLK',-12.7,60.96,90,'input'),pin('SWGND','SWD_GND',0,60.96,90),pin('SWDIO','SWDIO',12.7,60.96,90,'bidirectional')]
    box_symbol('AHCT125',[(1,'/1OE','input'),(2,'1A','input'),(4,'/2OE','input'),(5,'2A','input'),(10,'/3OE','input'),(9,'3A','input'),(13,'/4OE','input'),(12,'4A','input')],[(3,'1Y','tri_state'),(6,'2Y','tri_state'),(8,'3Y','tri_state'),(11,'4Y','tri_state'),(14,'VCC','power_in'),(7,'GND','power_in')],48.26,5.08,48.26)
    box_symbol('OLED938',[(f'H{i}',n) for i,n in enumerate(['SDA','SCL','DC_SA0','RST','CS','3V_OUT','VIN','GND'],1)],[(f'QA{i}',n,'power_in' if i in [1,2] else 'bidirectional') for i,n in enumerate(['QT1_GND','QT1_VIN','QT1_SDA','QT1_SCL'],1)]+[(f'QB{i}',n) for i,n in enumerate(['QT2_GND','QT2_VIN','QT2_SDA','QT2_SCL'],1)],71.12,5.08,53.34)
    box_symbol('RTC3013',[(1,'VIN','power_in'),(2,'GND','power_in'),(3,'SCL','input'),(4,'SDA','bidirectional')],[(5,'BAT'),(6,'32K','open_collector'),(7,'SQW','open_collector'),(8,'RST','open_collector')],71.12,5.08,33.02)
    box_symbol('BOB15100',[],[(1,'CC2'),(2,'D+'),(3,'D-'),(4,'CC1'),(5,'GND'),(6,'VBUS')],55.88,5.08,45.72)
    box_symbol('ServoJR',[(1,'GND'),(2,'+5V'),(3,'SIGNAL')],[],43.18,5.08,25.4)
    box_symbol('XH7',[(1,'SERVO_GND'),(2,'SERVO_5V'),(3,'PITCH_SIG'),(4,'OLED_GND'),(5,'OLED_3V3'),(6,'OLED_SDA'),(7,'OLED_SCL')],[],50.8,5.08,45.72)

    power=Sheet(PROJECT,'NODI / power entry and distribution',1)
    power.text('FULL SYSTEM ELECTRICAL SCHEMATIC - REVISION B',20.32,17.78,3.048)
    power.text('Dedicated regulated 5.0-5.1 V / 3 A USB-C source only. No USB PD request and no current-advertisement detector.',20.32,27.94)
    power.text('All off-board interconnects: ../Wiring/NODI_Wiring_RevB.pdf. All individual pin nets: ../netlist.csv.',20.32,35.56)
    power.outline(17.78,48.26,152.4,132.08)
    power.text('EXTERNAL INSULATED INPUT POD / PURCHASED MODULE',22.86,55.88,1.778)
    power.add('J1','BOB15100','SparkFun BOB-15100 current Rd revision',68.58,93.98,{'1':'USB_CC2','4':'USB_CC1','5':'GND','6':'+5V_RAW'},'Module header J3 pad numbers from current official Eagle source; socket shield remains isolated',wired=(6,))
    power.add('R7','R_V','5.1k 1% included',111.76,149.86,{'1':'USB_CC1','2':'GND'},'ALREADY fitted on current J1 module; vendor R4; do not add parallel external resistor',False)
    power.add('R8','R_V','5.1k 1% included',147.32,149.86,{'1':'USB_CC2','2':'GND'},'ALREADY fitted on current J1 module; vendor R1; do not add parallel external resistor',False)
    power.text('R7/R8 shown to define the sink: they are inside J1 purchase.',22.86,172.72,1.27)
    power.add('F1','Fuse','2.5 A time-delay >=32 VDC',218.44,81.28,{'1':'+5V_RAW','2':'+5V_FUSED'},'Inline insulated holder; cable and fuse coordination untested',wired=(1,2))
    power.add('D1','Schottky','1N5819',312.42,81.28,{'2':'+5V_FUSED','1':'VSYS_EXT'},'Band / cathode points toward Pico VSYS pin39, never VBUS pin40',wired=(2,))
    power.add('C1','Cap_Polar','1000uF / 10V',210.82,134.62,{'1':'+5V_FUSED','2':'GND'},'Bulk capacitor maximum diameter10mm height16mm; observe polarity',wired=(1,))
    power.add('C2','Cap','100nF / >=10V',284.48,134.62,{'1':'+5V_FUSED','2':'GND'},'Ceramic at distribution rail',wired=(1,))
    power.wire((101.6,106.68),(180.34,106.68));power.wire((180.34,106.68),(180.34,81.28));power.wire((180.34,81.28),(210.82,81.28));power.label('+5V_RAW',180.34,106.68)
    power.wire((226.06,81.28),(259.08,81.28));power.wire((259.08,81.28),(304.8,81.28));power.junction(259.08,81.28)
    power.wire((259.08,81.28),(259.08,121.92));power.junction(259.08,121.92);power.label('+5V_FUSED',259.08,121.92)
    power.wire((210.82,127),(210.82,121.92));power.wire((210.82,121.92),(259.08,121.92));power.wire((259.08,121.92),(284.48,121.92));power.wire((284.48,121.92),(284.48,127))
    power.add('TP1','Testpoint','+5V solder star',350.52,129.54,{'1':'+5V_FUSED'},'Covered 3A-rated solder distribution point; not a separate fabricated PCB part',False)
    power.add('TP2','Testpoint','GND solder star',350.52,165.1,{'1':'GND'},'Separate motor and logic returns meet here',False)
    for ref,net,x,y in [('#FLG01','+5V_FUSED',198.12,187.96),('#FLG02','VSYS_EXT',274.32,187.96),('#FLG03','GND',350.52,187.96)]:power.add(ref,'Flag','',x,y,{'1':net},'ERC source assertion: external dedicated adapter through fuse/diode; not a physical part',False)
    power.text('D1 and Pico onboard USB diode OR the sources. External +5V must not connect to U1 pin40 VBUS.',185.42,208.28,1.27)
    power.child('Controller_Interfaces','Controller, display, RTC and button',2,25.4,231.14)
    power.child('Motion_Audio','Actuators, buffer and piezo driver',3,226.06,220.98)

    ctl=Sheet('Controller_Interfaces','NODI / controller and user interfaces',2)
    ctl.text('CONTROLLER AND MODULE EXTERNAL PINS',20.32,17.78,3.048)
    ctl.text('NC crosses mean no EXTERNAL wire. Purchased modules contain onboard connections and pullups not expanded here.',20.32,27.94)
    ctl.add('U1','Pico','Raspberry Pi Pico / original RP2040',86.36,104.14,{'3':'GND','4':'YAW_PWM_3V3','5':'PITCH_PWM_3V3','6':'I2C_SDA','7':'I2C_SCL','20':'BUTTON_N','21':'AUDIO_PWM_3V3','36':'+3V3','39':'VSYS_EXT'},'Physical header numbers; other GND pads internally common on Pico; use pin3 external return')
    ctl.text('U1 programming micro-USB is ONBOARD; use its normal data cable.',20.32,180.34,1.27)
    ctl.text('U1 pin40 VBUS left externally NC. SWD pads unused.',20.32,187.96,1.27)
    ctl.add('U3','OLED938','Adafruit 938 / current STEMMA QT',287.02,93.98,{'QA1':'GND','QA2':'+3V3','QA3':'I2C_SDA','QA4':'I2C_SCL'},'H1..H8 are vendor JP2 header pad1..8; QA1..4 are QT connector1 pins; QB is second unused QT connector')
    ctl.text('Use QT1 only: pin1 GND,2 VIN,3 SDA,4 SCL. Header H1..H8 and QT2 unused externally.',205.74,134.62,1.27)
    ctl.text('Default I2C solder jumpers closed. RST auto-reset; DC/SA0 and CS need no external wire.',205.74,142.24,1.27)
    ctl.text('U3 address0x3D or0x3C; firmware probes both. Do not connect H6 regulator output to VIN.',205.74,149.86,1.27)
    ctl.add('U4','RTC3013','Adafruit 3013 / DS3231 non-QT',287.02,205.74,{'1':'+3V3','2':'GND','3':'I2C_SCL','4':'I2C_SDA'},'Vendor JP1 header pin1..8. BAT header intentionally unused; CR1220 installs into ONBOARD holder')
    ctl.text('BT1: non-rechargeable CR1220 inserted in U4 onboard holder; no loose battery wires.',205.74,233.68,1.27)
    ctl.text('BAT,32K,SQW,RST pads left externally NC. Module includes 10k I2C pullups to VIN.',205.74,241.3,1.27)
    ctl.add('SW1','Tactile4','Adafruit1119 / normally open',81.28,226.06,{'A1':'BUTTON_N','A2':'BUTTON_N','B1':'GND','B2':'GND'},'Project terminal labels A1/A2 are one common pair; B1/B2 other pair; verify continuity before wiring')
    ctl.text('GP15 internal INPUT_PULLUP. Wire one A terminal and one B terminal;',20.32,254,1.27)
    ctl.text('the second terminal of each pair is internally common, not another cable wire.',20.32,261.62,1.27)

    motion=Sheet('Motion_Audio','NODI / actuators and sound',3)
    motion.text('SERVO BUFFER, ALL TIES, AND DISCRETE AUDIO DRIVER',20.32,17.78,3.048)
    motion.text('GPIO numbers and physical U1 pins match Firmware/NODI/NODI.ino. Hardware, rail droop and startup remain untested.',20.32,27.94)
    motion.add('U2','AHCT125','SN74AHCT125N / PDIP14',71.12,78.74,{'1':'GND','2':'YAW_PWM_3V3','4':'GND','5':'PITCH_PWM_3V3','10':'+5V_FUSED','9':'GND','13':'+5V_FUSED','12':'GND','3':'YAW_BUFFER_5V','6':'PITCH_BUFFER_5V','14':'+5V_FUSED','7':'GND'},'AHCT TTL inputs; not HC. Unused outputs3Y/4Y NC; unused inputs tied; inputs tolerate5.5V atVCC0 per TIRevR5.4')
    motion.add('R1','R_H','220R',152.4,53.34,{'1':'YAW_BUFFER_5V','2':'YAW_SIG'},'Series servo signal resistor')
    motion.add('R2','R_H','220R',152.4,93.98,{'1':'PITCH_BUFFER_5V','2':'PITCH_SIG'},'Series servo signal resistor')
    motion.add('J2','ServoJR','Yaw servo / MG90S',238.76,63.5,{'1':'GND','2':'+5V_FUSED','3':'YAW_SIG'},'Project mating-face numbering:1GND,2supply,3signal. Check actual servo wiring; vendor plug has no guaranteed molded numbers')
    motion.add('J3','ServoJR','Pitch servo / MG90S',353.06,63.5,{'1':'GND','2':'+5V_FUSED','3':'PITCH_SIG'},'Moving servo case; cable via J4; project mating-face numbering1GND2supply3signal')
    motion.add('R3','R_V','100k',25.4,147.32,{'1':'YAW_PWM_3V3','2':'GND'},'Input pulldown at U2')
    motion.add('R4','R_V','100k',86.36,147.32,{'1':'PITCH_PWM_3V3','2':'GND'},'Input pulldown at U2')
    motion.add('C3','Cap','100nF',147.32,147.32,{'1':'+5V_FUSED','2':'GND'},'Ceramic directly across U2 pin14 and7')
    motion.add('J4','XH7','JST B7B-XH-A / XHP-7 harness',269.24,147.32,{'1':'GND','2':'+5V_FUSED','3':'PITCH_SIG','4':'GND','5':'+3V3','6':'I2C_SDA','7':'I2C_SCL'},'Base header and mating XHP-7 housing; SXH-001T-P0.6 contacts; separate servo/display ground conductors')
    motion.text('J4 is the fixed-base disconnect. Seven wires form one loose rear service loop;',198.12,185.42,1.27)
    motion.text('split into J3 three-wire servo lead and U3 QT1 four-wire display lead in head.',198.12,193.04,1.27)
    motion.text('Do not feed +5V servo power through Pico, QT cable, or regulator.',20.32,180.34,1.27)
    motion.add('R5','R_H','4.7k',60.96,226.06,{'1':'AUDIO_PWM_3V3','2':'PIEZO_BASE'},'Base current resistor; GPIO3.3V, about0.55mA atVBE0.7V',wired=(2,))
    motion.add('R6','R_V','100k',119.38,246.38,{'1':'PIEZO_BASE','2':'GND'},'Q1 base-emitter pulldown',wired=(1,))
    motion.add('Q1','NPN','onsemi 2N3904G / TO-92',198.12,233.68,{'1':'GND','2':'PIEZO_BASE','3':'PIEZO_SW'},'Physical pin1E2B3C for selected onsemi package; inspect actual package orientation',wired=(2,3))
    motion.add('BZ1','Piezo','PKM13EPYH4000-A0',294.64,238.76,{'1':'+5V_FUSED','2':'PIEZO_SW'},'External-drive PIEZO, not magnetic.4kHz; no inductive flyback diode required',wired=(1,2))
    motion.add('R9','R_V','1k',363.22,238.76,{'1':'+5V_FUSED','2':'PIEZO_SW'},'Piezo discharge resistor parallel to BZ1; about5mA while Q1 on')
    motion.wire((68.58,226.06),(119.38,226.06));motion.wire((119.38,226.06),(167.64,226.06));motion.wire((167.64,226.06),(167.64,233.68));motion.wire((167.64,233.68),(190.5,233.68));motion.junction(119.38,226.06)
    motion.wire((119.38,226.06),(119.38,238.76));motion.label('PIEZO_BASE',119.38,226.06)
    motion.wire((203.2,226.06),(259.08,226.06));motion.wire((259.08,226.06),(259.08,246.38));motion.wire((259.08,246.38),(294.64,246.38));motion.wire((294.64,246.38),(363.22,246.38));motion.junction(294.64,246.38);motion.junction(363.22,246.38)
    motion.wire((294.64,231.14),(363.22,231.14));motion.junction(363.22,231.14)
    motion.text('R9 and BZ1 are parallel. Q1 sinks the piezo negative terminal; emitter always GND.',198.12,266.7,1.27)
    for sheet in [power,ctl,motion]:sheet.write()
    (SCHEM/'NODI_System.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator "nodi-electrical-generator")\n'+"\n".join(library_definition(k,False) for k in sorted(LIB))+')\n')
    (SCHEM/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "NODI") (type "KiCad") (uri "${KIPRJMOD}/NODI_System.kicad_sym") (options "") (descr "NODI self-contained system symbols")))\n')
    for name,rows,fields in [('netlist.csv',PINS,['reference','pin','pin_name','net','electrical_type','sheet','notes']),('schematic_components.csv',COMPONENTS,['ref','value','symbol','sheet','notes','in_bom'])]:
        with (HERE/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
    print(f'Generated 3 KiCad sheets, {len(COMPONENTS)} symbols, {len(PINS)} explicit pins, {len({p["net"] for p in PINS if p["net"]!="NC"})} named nets')

def build_wiring():
    """Physical wires, rather than every logical node inside an assembled module."""
    # ref/pin pairs use native schematic identifiers; lengths are cut allowances,
    # NOT measurements. Carrier-local passives are completely defined in KiCad.
    specs=[
      ('J1','6','F1','1','+5V_RAW','red',20,300,False,'External insulated input pod to captive cable; dedicated3A source'),
      ('J1','5','TP2','1','GND','black',20,300,False,'Main return; protect through rear sleeve and mechanical tie'),
      ('F1','2','TP1','1','+5V_FUSED','red',20,60,False,'Covered solder star, not a Pico supply pin'),
      ('TP1','1','J2','2','+5V_FUSED','red',24,80,False,'Yaw servo supply, independent branch'),
      ('TP2','1','J2','1','GND','black',24,80,False,'Yaw servo return, independent branch'),
      ('R1','2','J2','3','YAW_SIG','purple',26,80,False,'After220ohm series resistor'),
      ('TP1','1','J4','2','+5V_FUSED','red',24,90,False,'Pitch branch to fixed-base disconnect'),
      ('TP2','1','J4','1','GND','black',24,90,False,'Pitch motor return; not shared with thin OLED wire'),
      ('R2','2','J4','3','PITCH_SIG','green',26,90,False,'After220ohm series resistor'),
      ('U1','36','J4','5','+3V3','orange',28,90,False,'OLED VIN; electrically3.3V even though QT cable color may be red'),
      ('TP2','1','J4','4','GND','black',28,90,False,'Separate OLED return conductor'),
      ('U1','6','J4','6','I2C_SDA','blue',28,90,False,'GP4 physicalpin6'),
      ('U1','7','J4','7','I2C_SCL','yellow',28,90,False,'GP5 physicalpin7'),
      ('J4','1','J3','1','GND','black',24,180,True,'Moving motor return; at least80mm free loop after fit'),
      ('J4','2','J3','2','+5V_FUSED','red',24,180,True,'Moving motor supply; do not confuse with OLED VIN'),
      ('J4','3','J3','3','PITCH_SIG','green',26,180,True,'Moving motor signal; verify installed pitch polarity'),
      ('J4','4','U3','QA1','GND','black',28,180,True,'QT1 pin1 ground'),
      ('J4','5','U3','QA2','+3V3','orange',28,180,True,'QT1 pin2 VIN; stock QT lead red is3.3V on this circuit'),
      ('J4','6','U3','QA3','I2C_SDA','blue',28,180,True,'QT1 pin3 SDA'),
      ('J4','7','U3','QA4','I2C_SCL','yellow',28,180,True,'QT1 pin4 SCL'),
      ('U1','36','U4','1','+3V3','orange',28,70,False,'RTC VIN headerpin1, not BATpin5'),
      ('TP2','1','U4','2','GND','black',28,70,False,'RTC GND headerpin2'),
      ('U1','6','U4','4','I2C_SDA','blue',28,70,False,'RTC SDA headerpin4'),
      ('U1','7','U4','3','I2C_SCL','yellow',28,70,False,'RTC SCL headerpin3'),
      ('U1','20','SW1','A1','BUTTON_N','white',28,100,False,'GP15 to one terminal of common pairA; internal INPUT_PULLUP'),
      ('TP2','1','SW1','B1','GND','black',28,100,False,'One terminal of opposite common pairB; other two legs need no wires'),
      ('U1','4','U2','2','YAW_PWM_3V3','purple',28,80,False,'GP2 to AHCT1A; R3 pulls this node down'),
      ('U1','5','U2','5','PITCH_PWM_3V3','green',28,80,False,'GP3 to AHCT2A; R4 pulls this node down'),
      ('U1','21','R5','1','AUDIO_PWM_3V3','brown',28,80,False,'GP16 physicalpin21; R5 is4.7k base series'),
      ('TP1','1','BZ1','1','+5V_FUSED','red',28,70,False,'Piezo positive; R9 parallel between +5V and Q1collector'),
      ('Q1','3','BZ1','2','PIEZO_SW','brown',28,70,False,'Piezo negative to onsemi Q1collector pin3'),
      ('TP1','1','U2','14','+5V_FUSED','red',24,40,False,'AHCT VCC; C3 local across14/7'),
      ('TP2','1','U2','7','GND','black',24,40,False,'AHCT GND; channel OE and input ties local per schematic'),
      ('TP1','1','D1','2','+5V_FUSED','red',24,40,False,'Schottky ANODE pin2'),
      ('D1','1','U1','39','VSYS_EXT','red',24,90,False,'Banded CATHODE pin1 to VSYS39; NEVER VBUS40'),
      ('TP2','1','U1','3','GND','black',24,90,False,'Single Pico return; all other Pico GND pads internally common'),
    ]
    fields=['wire_id','from_ref','from_pin','to_ref','to_pin','net','wire_color','awg','cut_length_mm','moving','notes']
    rows=[dict(zip(fields,[f'W{i:02}',*a[:-1],a[-1]])) for i,a in enumerate(specs,1)]
    with (HERE/'wiring_schedule.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
    colors={'red':'#c63e35','black':'#202731','orange':'#cf741c','purple':'#7854a3','green':'#267b4c','blue':'#2176b8','yellow':'#ad8b00','white':'#6d7988','brown':'#805339'}
    width=1600; row_h=42; footer=180+len(rows)*row_h; height=footer+900
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><title>NODI complete pin-to-pin harness RevB</title><rect width="100%" height="100%" fill="white"/>', '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#243746}.h{font-size:34px;font-weight:bold}.sub{font-size:19px}.t{font-size:18px}.small{font-size:16px}.bold{font-weight:bold}</style>', '<text x="45" y="52" class="h">NODI / full pin-to-pin wiring / revision B</text>','<text x="45" y="87" class="sub">2026-10-25 · actual schematic pin IDs · all hardware untested · local passive wiring: three-sheet KiCad circuit</text>','<text x="45" y="119" class="sub">Lengths below are initial cut allowances, not measured fits. Seven moving wires W14–W20 need ≥80 mm free loop.</text>','<text x="45" y="151" class="small">ID / source pin</text><text x="560" y="151" class="small">net / color</text><text x="1060" y="151" class="small">destination pin / wire size / cut length</text>']
    for i,r in enumerate(rows):
        y=180+i*row_h;c=colors[r['wire_color']]
        if i%2==0:s.append(f'<rect x="32" y="{y-24}" width="1535" height="40" fill="#f4f7f8"/>')
        s.append(f'<text x="45" y="{y}" class="t bold">{r["wire_id"]}  {r["from_ref"]}.{r["from_pin"]}</text><line x1="330" y1="{y-7}" x2="990" y2="{y-7}" stroke="{c}" stroke-width="4"/><polygon points="990,{y-12} 1000,{y-7} 990,{y-2}" fill="{c}"/><rect x="485" y="{y-23}" width="355" height="29" fill="white"/><text x="500" y="{y}" class="t">{html.escape(r["net"])} / {r["wire_color"]}</text><text x="1060" y="{y}" class="t">{r["to_ref"]}.{r["to_pin"]} · {r["awg"]} AWG · {r["cut_length_mm"]} mm'+(' · FLEX' if r['moving'] else '')+'</text>')
    def tx(x,y,text,cl='t'):s.append(f'<text x="{x}" y="{y}" class="{cl}">{html.escape(text)}</text>')
    tx(45,footer+15,'CONNECTOR VIEWS AND ASSEMBLY RULES','h')
    tx(45,footer+53,'J4 JST XH: mating-face PROJECT cavity numbering; identify molded cavity 1 and continuity-check before inserting contacts.','sub')
    for i,label in enumerate(['1 GND','2 +5V','3 PITCH','4 GND','5 +3V3','6 SDA','7 SCL']):
        x=65+i*205;s.append(f'<rect x="{x}" y="{footer+78}" width="190" height="58" rx="4" fill="#edf2f4" stroke="#344a5c"/>');tx(x+15,footer+114,label)
    tx(45,footer+173,'View from WIRE ENTRY reverses left/right. Use circuit/cavity IDs, not a guessed mirror of a product photograph.','small')
    tx(45,footer+224,'J2 / J3 servo plugs','sub');tx(45,footer+254,'Mating face, project numbers:  [1 GND] [2 +5V] [3 SIG]','t');tx(45,footer+284,'Verify servo brown/black=GND, red=+5V, orange/yellow=signal.','small')
    tx(830,footer+224,'U3 STEMMA QT / JST SH 4','sub');tx(830,footer+254,'[1 GND] [2 VIN=3.3V] [3 SDA] [4 SCL]','t');tx(830,footer+284,'Stock QT red lead carries 3.3V here. Do not connect servo +5V.','small')
    tx(45,footer+338,'J1 BOB-15100 component-side view, USB socket LEFT:','sub');tx(45,footer+368,'Header TOP→BOTTOM: 6 VBUS, 5 GND, 4 CC1, 3 D−, 2 D+, 1 CC2.','t');tx(45,footer+398,'Current board already has 2 × 5.1k Rd. Do not parallel extra CC resistors.','small')
    tx(830,footer+338,'SW1 four-leg switch / continuity labels','sub');tx(830,footer+368,'A1—A2 are common; B1—B2 are common. Press joins A to B.','t');tx(830,footer+398,'Wire W25 to A1 and W26 to B1; verify pairs with an ohmmeter.','small')
    for i,t in enumerate(['No arbitrary computer USB port: dedicated 5.0–5.1V / 3A source. Main supply/return20AWG; servo branches24AWG; signal26/28AWG.','J4 header + XHP-7 housing + SXH-001T-P0.6 contacts form an insulated fixed-base disconnect; its retention and exact fit are not modeled.','Carrier-local wiring (R1–R9, C1–C3, D1, Q1 and U2 ties) is fully defined in the native circuit and netlist, not omitted from the electrical design.','Inspect polarity and shorts before power. Center servos with horns removed. Require a physical harness sweep, cable pull test and supply droop test.']):tx(45,footer+463+i*36,t,'small')
    # A physical four-leg view supplements the logical switch symbol.
    tx(45,footer+643,'SW1 physical top view; rotate to put continuity-identified common pairs at left and right.','sub')
    s.append(f'<rect x="220" y="{footer+674}" width="220" height="130" rx="8" fill="#edf2f4" stroke="#344a5c"/><circle cx="330" cy="{footer+739}" r="29" fill="#586c79"/>')
    for x,label1,label2 in [(170,'A1 / W25','A2 / no wire'),(490,'B1 / W26','B2 / no wire')]:
        for y,label in [(footer+697,label1),(footer+782,label2)]:
            s.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#243746"/><line x1="{x}" y1="{y}" x2="{220 if x<220 else 440}" y2="{y}" stroke="#243746" stroke-width="3"/>');tx(x-90 if x<220 else x+18,y-12,label,'small')
        s.append(f'<line x1="{x}" y1="{footer+697}" x2="{x}" y2="{footer+782}" stroke="#327d88" stroke-width="4"/>')
    tx(740,footer+704,'Pair A is internally common; pair B is internally common.','t');tx(740,footer+742,'No terminal numbering is assumed from an anonymous switch photo.','small');tx(740,footer+780,'Use an ohmmeter; pressing must join A to B.','t')
    s.append('</svg>');(WIRING/'NODI_Wiring_RevB.svg').write_text('\n'.join(s))
    # Standard A3 vector PDF, rather than a single impractically tall print page.
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A3,landscape
        from reportlab.lib.colors import HexColor
        c=canvas.Canvas(str(WIRING/'NODI_Wiring_RevB.pdf'),pagesize=landscape(A3));pw,ph=landscape(A3)
        def text(x,y,t,size=10,bold=False):c.setFillColor(HexColor('#243746'));c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,t)
        for page,start in enumerate([0,18]):
            text(40,ph-48,'NODI / PIN-TO-PIN WIRING / REV B',22,True);text(40,ph-72,'25 October 2026 | Hardware untested | Cut lengths are allowances; trim after physical dry fit.',11)
            text(40,ph-101,'SOURCE PIN',10,True);text(393,ph-101,'NET / COLOR',10,True);text(820,ph-101,'DESTINATION / GAUGE / CUT LENGTH',10,True)
            for i,r in enumerate(rows[start:start+18]):
                y=ph-132-i*33
                if i%2==0:c.setFillColor(HexColor('#f3f6f7'));c.rect(30,y-10,pw-60,30,fill=1,stroke=0)
                text(40,y,r['wire_id']+'  '+r['from_ref']+'.'+r['from_pin'],11,True)
                c.setStrokeColor(HexColor(colors[r['wire_color']]));c.setLineWidth(2);c.line(230,y+4,790,y+4)
                c.setFillColor(HexColor('#ffffff'));c.rect(366,y-5,245,19,fill=1,stroke=0)
                text(378,y,r['net']+' / '+r['wire_color'],10)
                text(820,y,f"{r['to_ref']}.{r['to_pin']}   {r['awg']} AWG   {r['cut_length_mm']} mm"+('   FLEX' if r['moving'] else ''),10)
            text(40,58,'W14-W20: >=80mm free moving loop. Pin numbers are circuit/cavity IDs; see connector rules on page3.',10)
            text(40,38,'Local passives and IC ties: NODI_System_RevB.pdf. Detailed wire notes: ../wiring_schedule.csv.',10)
            text(pw-110,38,f'{page+1} / 4',10);c.showPage()
        text(40,ph-48,'NODI / CONNECTOR VIEWS AND FABRICATION NOTES',20,True)
        notes=[
            ('J4 / seven-way fixed-base disconnect','JST B7B-XH-A header + XHP-7 housing + SXH-001T-P0.6 contacts. Match molded cavity1.','Mating-face project cavity sequence: 1 servoGND | 2 +5V | 3 pitchSIG | 4 OLEDGND | 5 +3V3 | 6 SDA | 7 SCL.'),
            ('J2 / J3 / servo plug mating faces','Project numbering: [1 GND] [2 +5V] [3 SIG]. Center contact is supply.','Verify actual servo colors and continuity; vendor JR plugs have no assumed molded integer numbering.'),
            ('U3 / STEMMA QT','Physical connector contacts: [1 GND] [2 VIN=3.3V] [3 SDA] [4 SCL].','QT wire colors: black GND; red VIN (3.3V in NODI); blue SDA; yellow SCL. Other module header pins NC.'),
            ('J1 / USB-C input board component-side view','USB socket LEFT; six-pad header TOP to BOTTOM: 6 VBUS, 5 GND, 4 CC1, 3 D-, 2 D+, 1 CC2.','Current BOB-15100 already contains two5.1k Rd. Do not fit parallel external CC resistors.'),
            ('SW1 / all four physical legs','Project labels A1/A2 identify one internally common pair; B1/B2 the other. Press joins A to B.','Wire one A leg and one B leg. Do not use two legs from the same pair; verify pairs using continuity mode.'),
            ('Construction scope','TP1/TP2 are covered solder-star joints. Use separate motor returns; do not route servo power through Pico.','J4 is an insulated tethered disconnect: no fit/retention claim in current CAD. Input pod is outside the base.'),
            ('Before powering','Continuity-check every CSV wire; inspect shorts, polarity, fuse, cathode band, transistor pinout and module revision.','Power current-limited without servos, then center with horns removed. Sweep all combined poses before live motion.'),
        ]
        y=ph-100
        for title,a,b in notes:
            text(40,y,title,13,True);text(40,y-22,a,10);text(40,y-40,b,10);y-=84
        text(40,54,'Connector views are functional project diagrams, not scaled machining drawings. Wire-entry views mirror mating faces.',10)
        text(40,36,'No hardware build, electrical measurement or harness fatigue test has been performed.',10);text(pw-110,36,'3 / 4',10);c.showPage()
        text(40,ph-48,'NODI / PHYSICAL CONNECTOR PIN MAPS',22,True)
        text(40,ph-72,'Functional views: not scaled drawings. Match molded pad1 or project marks; wire-entry views mirror mating faces.',10)
        # Original Pico component-side top view with micro-USB toward page top.
        bx,by,bw,bh=80,140,215,550;c.setStrokeColor(HexColor('#344a5c'));c.setFillColor(HexColor('#edf2f4'));c.roundRect(bx,by,bw,bh,8,fill=1,stroke=1);c.rect(bx+75,by+bh-18,65,30,fill=0,stroke=1)
        text(bx,by+bh+26,'U1 / PICO / USB UP',13,True)
        used={3:'GND',4:'GP2 YAW',5:'GP3 PITCH',6:'GP4 SDA',7:'GP5 SCL',20:'GP15 BUTTON',21:'GP16 AUDIO',36:'3V3 OUT',39:'VSYS'}
        for i in range(20):
            yy=by+bh-40-i*25
            for pn,xx,dx in [(i+1,bx+10,18),(40-i,bx+bw-10,-90)]:
                c.setFillColor(HexColor('#327d88' if pn in used else '#aeb8be'));c.circle(xx,yy,3.5,fill=1,stroke=0);text(xx+dx,yy-3,str(pn)+' '+used.get(pn,'NC'),8)
        text(bx,by-25,'Other GND pads are internally common; pin3 is external return.',9)
        # SparkFun layout-derived view, socket at left, header down right.
        x,y=420,490;c.setFillColor(HexColor('#edf2f4'));c.roundRect(x,y,205,180,6,fill=1,stroke=1);c.setFillColor(HexColor('#ced6dc'));c.rect(x-24,y+55,55,70,fill=1,stroke=1);text(x,y+205,'J1 / COMPONENT SIDE',13,True);text(x-20,y+140,'USB socket LEFT',9)
        for i,t in enumerate(['6 VBUS','5 GND','4 CC1','3 D- NC','2 D+ NC','1 CC2']):c.setFillColor(HexColor('#327d88'));c.circle(x+165,y+150-i*25,4,fill=1,stroke=0);text(x+178,y+147-i*25,t,9)
        # J4 mating face, orient by molded cavity1, rather than guessed photo.
        x,y=760,570;text(x,y+120,'J4 / MATING OPENINGS TOWARD YOU',12,True);text(x,y+101,'Orient molded cavity1 at LEFT. Back/wire-entry view is mirrored.',9)
        for i,t in enumerate(['1','2','3','4','5','6','7']):c.setFillColor(HexColor('#edf2f4'));c.rect(x+i*47,y,44,58,fill=1,stroke=1);text(x+i*47+17,y+24,t,13,True)
        text(x,y-20,'GND | +5V | SIG | GND | +3V3 | SDA | SCL',10)
        # The actual four-leg switch: two internally common terminal pairs.
        x,y=455,240;text(x-30,y+160,'SW1 / TOP VIEW / VERIFY PAIRS BY CONTINUITY',12,True);c.setFillColor(HexColor('#edf2f4'));c.roundRect(x,y,150,110,6,fill=1,stroke=1);c.setFillColor(HexColor('#596d79'));c.circle(x+75,y+55,22,fill=1,stroke=0)
        for xx,pair in [(x-35,'A'),(x+185,'B')]:
            c.setStrokeColor(HexColor('#327d88'));c.setLineWidth(2);c.line(xx,y+18,xx,y+92)
            for yy,n in [(y+92,'1'),(y+18,'2')]:c.circle(xx,yy,4,fill=0,stroke=1);c.line(xx,yy,x if pair=='A' else x+150,yy);text(xx-25 if pair=='A' else xx+12,yy+5,pair+n,10,True)
        text(x-50,y-28,'W25 to A1; W26 to B1. A2/B2 require no additional wires.',9)
        # Servo JR physical sequence is project-defined, not vendor molded ID.
        x,y=790,300;text(x,y+100,'J2 / J3 / SERVO MATING FACE',12,True)
        for i,t in enumerate(['1 GND','2 +5V','3 SIG']):c.setFillColor(HexColor('#edf2f4'));c.rect(x+i*90,y,85,55,fill=1,stroke=1);text(x+8+i*90,y+23,t,10,True)
        text(x,y-24,'Mark GND on housing; confirm the actual servo lead colors.',9)
        text(40,65,'The pin maps supplement the circuit: supply voltage and cavity continuity must be checked before energizing.',10)
        text(40,44,'J4 is an unmodeled, separately insulated/tethered disconnect; XH2.50mm pitch is not standard2.54mm perfboard pitch.',10);text(pw-110,44,'4 / 4',10);c.save()
    except ImportError:
        raise SystemExit('PDF requires reportlab; install requirements.txt and regenerate before exporting.')
    print(f'Generated {len(rows)} explicit physical wires and connector-view wiring SVG/PDF')

if __name__=='__main__':
    SCHEM.mkdir(exist_ok=True);WIRING.mkdir(exist_ok=True);build();build_wiring()
