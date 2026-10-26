#!/usr/bin/env python3
"""Run real KiCad exports/ERC, then bind exact source/output hashes.

This is the only script that refreshes export_provenance.json. The fast verifier
never silently rebinds edited sources to stale exports.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
SOURCE_FILES=[
    'generate_electrical.py','electronics_BOM.csv','netlist.csv','schematic_components.csv','wiring_schedule.csv',
    'Schematics/NODI_System_RevB.kicad_sch','Schematics/Controller_Interfaces.kicad_sch',
    'Schematics/Motion_Audio.kicad_sch','Schematics/NODI_System.kicad_sym',
    'Schematics/NODI_System_RevB.kicad_pro','Schematics/sym-lib-table',
    'Wiring/NODI_Wiring_RevB.svg','Wiring/NODI_Wiring_RevB.pdf',
]
OUTPUT_FILES=['Schematics/NODI_System_RevB.net','Schematics/erc_report.json','Schematics/NODI_System_RevB.pdf']
def digest(name):return hashlib.sha256((HERE/name).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--launcher',help='Optional AppImage AppRun executable; default is installed kicad-cli');args=p.parse_args()
    cli=[str(Path(args.launcher).resolve()),'kicad-cli'] if args.launcher else ['kicad-cli']
    version=subprocess.run(cli+['version'],check=True,capture_output=True,text=True).stdout.strip()
    commands=[['sch','export','netlist','--format','kicadxml','-o',OUTPUT_FILES[0],'Schematics/NODI_System_RevB.kicad_sch'],
              ['sch','erc','--format','json','--severity-all','--exit-code-violations','-o',OUTPUT_FILES[1],'Schematics/NODI_System_RevB.kicad_sch'],
              ['sch','export','pdf','-o',OUTPUT_FILES[2],'Schematics/NODI_System_RevB.kicad_sch']]
    before={name:digest(name) for name in SOURCE_FILES}
    for command in commands:subprocess.run(cli+command,cwd=HERE,check=True)
    after={name:digest(name) for name in SOURCE_FILES}
    assert before==after,'Sources changed during export; rerun against a frozen source set'
    report=json.loads((HERE/OUTPUT_FILES[1]).read_text())
    assert not [v for s in report.get('sheets',[]) for v in s.get('violations',[])],'ERC reported violations'
    result=dict(exported_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kicad_version=version,
        commands=[['kicad-cli']+c for c in commands],sources_sha256=after,
        outputs_sha256={name:digest(name) for name in OUTPUT_FILES},hardware_tested=False)
    (HERE/'export_provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Bound frozen source/output hashes after actual KiCad netlist, ERC and PDF execution.')
if __name__=='__main__':main()
