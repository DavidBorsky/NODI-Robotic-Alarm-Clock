#!/usr/bin/env python3
"""Audit actual KiCad-exported connectivity against the intended CSV and firmware.

This is a reproducible schema/connectivity audit, not an ERC substitute or a
physical electrical test. Rerun KiCad export/ERC after editing the schematic.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
def read_csv(name):
    with (HERE/name).open(newline='') as f:return list(csv.DictReader(f))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    provenance=json.loads((HERE/'export_provenance.json').read_text())
    for category in ['sources_sha256','outputs_sha256']:
        for name,expected_digest in provenance[category].items():
            assert sha(HERE/name)==expected_digest,'Stale electrical source/export: '+name+'; regenerate then run real KiCad export_electrical.py'
    expected=read_csv('netlist.csv');wires=read_csv('wiring_schedule.csv')
    native=ET.parse(HERE/'Schematics/NODI_System_RevB.net').getroot()
    actual={}
    for net in native.findall('./nets/net'):
        for node in net.findall('node'):
            key=(node.get('ref'),node.get('pin'))
            assert key not in actual,'Pin appears on multiple KiCad nets: '+str(key)
            actual[key]=net.get('name')
    wanted={(p['reference'],p['pin']):p['net'] for p in expected if not p['reference'].startswith('#')}
    assert set(actual)==set(wanted),f'Pin set differs: missing {set(wanted)-set(actual)}, extra {set(actual)-set(wanted)}'
    for key,net in wanted.items():
        assert actual[key]==net if net!='NC' else actual[key].startswith('unconnected-'),f'KiCad connection differs at {key}: {actual[key]} != {net}'
    for w in wires:
        a=(w['from_ref'],w['from_pin']);b=(w['to_ref'],w['to_pin'])
        assert a in actual and b in actual,'Unknown harness endpoint: '+w['wire_id']
        assert actual[a]==actual[b]==w['net'],'Harness joins unlike nets: '+w['wire_id']
        assert 20<=int(w['awg'])<=28 and int(w['cut_length_mm'])>0
    moving=[w for w in wires if w['moving']=='True']
    assert len(moving)==7 and {w['wire_id'] for w in moving}=={f'W{i:02}' for i in range(14,21)}
    # Independent, explicit safety-critical interface expectations.
    fixed={('U1','4'):'YAW_PWM_3V3',('U1','5'):'PITCH_PWM_3V3',('U1','6'):'I2C_SDA',('U1','7'):'I2C_SCL',('U1','20'):'BUTTON_N',('U1','21'):'AUDIO_PWM_3V3',('U1','36'):'+3V3',('U1','39'):'VSYS_EXT',('D1','2'):'+5V_FUSED',('D1','1'):'VSYS_EXT',('U2','14'):'+5V_FUSED',('U2','7'):'GND',('U3','QA1'):'GND',('U3','QA2'):'+3V3',('U3','QA3'):'I2C_SDA',('U3','QA4'):'I2C_SCL',('U4','1'):'+3V3',('U4','2'):'GND',('U4','3'):'I2C_SCL',('U4','4'):'I2C_SDA',('Q1','1'):'GND',('Q1','2'):'PIEZO_BASE',('Q1','3'):'PIEZO_SW'}
    for key,net in fixed.items():assert actual[key]==net,f'Fixed interface mismatch {key}'
    assert actual[('U1','40')].startswith('unconnected-'),'External power accidentally joined Pico VBUS'
    for r in ['J2','J3']:assert [actual[(r,str(i))] for i in [1,2,3]]==['GND','+5V_FUSED','YAW_SIG' if r=='J2' else 'PITCH_SIG']
    for r in ['R7','R8']:assert actual[(r,'2')]=='GND'
    assert actual[('R7','1')]=='USB_CC1' and actual[('R8','1')]=='USB_CC2'
    firmware=(HERE.parent/'Firmware/NODI/NODI.ino').read_text()
    for name,gp in [('SDA_PIN',4),('SCL_PIN',5),('YAW_PIN',2),('PITCH_PIN',3),('BUTTON_PIN',15),('PIEZO_PIN',16)]:
        assert re.search(r'\b'+name+r'\s*=\s*'+str(gp)+r'\b',firmware),'Firmware pin changed: '+name
    erc=json.loads((HERE/'Schematics/erc_report.json').read_text())
    violations=[v for sheet in erc.get('sheets',[]) for v in sheet.get('violations',[])]
    assert not violations,'KiCad ERC has reported violations'
    inputs=[HERE/'Schematics'/f for f in ['NODI_System_RevB.kicad_sch','Controller_Interfaces.kicad_sch','Motion_Audio.kicad_sch','NODI_System.kicad_sym','NODI_System_RevB.net']]+[HERE/'netlist.csv',HERE/'wiring_schedule.csv',HERE.parent/'Firmware/NODI/NODI.ino']
    result=dict(date='2026-10-25',status='PASS',scope='actual KiCad XML versus expected CSV, physical wire endpoints and firmware GPIO constants; not physical testing',export_provenance_verified=True,kicad_version=erc.get('kicad_version'),schematic_sheets=3,schematic_symbols=30,explicit_pin_rows=len(expected),exported_connected_pins=sum(v!='NC' for v in wanted.values()),exported_nc_pins=sum(v=='NC' for v in wanted.values()),named_functional_nets=len(set(v for v in wanted.values() if v!='NC')),physical_wire_runs=len(wires),moving_conductors=len(moving),reported_erc_violations=len(violations),erc_ignored_checks=erc.get('ignored_checks',[]),hardware_tested=False,sha256={str(p.relative_to(HERE.parent)):sha(p) for p in inputs})
    (HERE/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"PASS: {len(wanted)} exported pins ({result['exported_connected_pins']} connected, {result['exported_nc_pins']} NC), {len(wires)} wires, 7 moving conductors, firmware GPIO map and KiCad ERC0.")
if __name__=='__main__':main()
