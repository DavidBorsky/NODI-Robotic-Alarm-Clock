#!/usr/bin/env python3
"""Reconcile CAD instances with electrical purchases and write the prototype BOM.

Costs are planning allowances, not quotes. The electrical input is authoritative
for electrical prices; printed material = solid CAD mass x $25/kg x 1.25 waste.
"""
import argparse
import csv
import io
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING = {
    "NODI-C02": "E02", "NODI-C06": "E03", "NODI-C07": "E01",
    "NODI-C08": "E04", "NODI-C09": "E20", "NODI-C10": "E11",
    "NODI-C11": "E08", "NODI-C12": "E06", "NODI-C13": "E07",
}
ALLOWANCES = {
    "NODI-C01": ("buy and finish", "1.00", "PTFE sheet washer OD40 / ID25 / thickness2 mm; cut and deburr"),
    "NODI-C03": ("buy and finish", "1.00", "19mm nylon disc horn; verify actual spline; drill1.8 and tapM2 on14mm pitch; additional allowance if servo kit horn unsuitable"),
    "NODI-C04": ("buy and finish", "1.00", "Brass tube OD4 / ID3.2; cut square to14.2mm; verify axial stack"),
    "NODI-C05": ("buy and finish", "0.40", "PTFE washer OD8 / ID4.3 / thickness1mm"),
    "NODI-C14": ("buy", "0.25", "Self-adhesive silicone foot diameter12mm thickness3mm; four positionsX+/-45,Y+/-44"),
    "NODI-P10": ("make", "5.00", "Low-carbon steel40x18x12.5;2holes3.4mm at28mm pitch; deburr and insulate from wiring; stock allowance excludes labor"),
    "NODI-F01": ("buy", "0.15", "M3x20 pan/socket head passive pivot screw; thread omitted from CAD"),
    "NODI-F02": ("buy", "0.15", "M3 DIN985 nylon-insert locking nut; nominal4mm axial envelope; install after sleeve"),
    "NODI-F03": ("buy", "0.10", "M3x10 deck screw; hand-tap printed2.7mm pilot; low-profile head fits CAD counterbore"),
    "NODI-F04": ("buy", "0.08", "M2x8 bezel screw; hand-tap printed1.8mm pilot"),
    "NODI-F05": ("buy", "0.08", "M2x5 OLED screw; hand-tap printed1.8mm pilot; do not stress glass"),
    "NODI-F06": ("buy", "0.08", "M2x8 servo mounting screw; four total two per servo; hand-tap printed1.8mm pilot"),
    "NODI-F07": ("buy", "0.08", "M2x6 horn screw; four total two per horn; tap nylon1.8mm holesM2"),
    "NODI-F08": ("buy", "0.10", "M3x6 rear/switch carrier screw; hand-tap printed2.7mm pilot"),
    "NODI-F09": ("buy - included", "0.00", "Vendor-supplied horn retaining screw; modeled M2.2x6 is nominal; use exact thread supplied with servo; included in E02 cost"),
    "NODI-F10": ("buy", "0.15", "M3x18 steel ballast screw; two; hand-tap2.7mm blind pilots; do not replace with adhesive"),
    "NODI-F11": ("buy", "0.10", "M3x5 power carrier screw; four; shorter length avoids floor breakthrough"),
}

def money(value):
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def render_bom():
    manifest = json.loads((ROOT / "CAD/manifest.json").read_text())
    with (ROOT / "Electronics/electronics_BOM.csv").open(newline="") as f:
        electrical = {row["ref"]: row for row in csv.DictReader(f)}
    groups = defaultdict(list)
    for item in manifest["instances"]:
        if item["part_number"] != "VISUAL": groups[item["part_number"]].append(item)
    rows, used_electrical = [], set()
    fields = ["part_number", "description", "make_or_buy", "quantity", "material_or_process",
              "estimated_unit_USD", "estimated_extended_USD", "cad_instance_ids",
              "electronics_ref", "cost_basis_and_notes"]
    for number, items in sorted(groups.items()):
        item = items[0]; count = len(items); ref = ""
        if number in MAPPING:
            ref = MAPPING[number]; entry = electrical[ref]; used_electrical.add(ref)
            # The OLED module is ONE purchase represented by PCB and glass solids.
            count = 1 if number == "NODI-C06" else count
            if count != int(entry["quantity"]):
                raise ValueError(f"CAD/electronics quantity mismatch: {number}")
            kind, unit = "buy", entry["estimated_unit_USD"]
            description = entry["description"]
            notes = entry["manufacturer_or_requirement"] + "; " + entry["status"]
            if number == "NODI-C06": notes += "; PCB and glass are one purchased module"
            if number == "NODI-C09": notes += "; kit includes wiring pads connectors and passives listed only where separately priced"
        elif item["printable"]:
            assert count == 1
            kind = "make"; description = item["name"]
            unit = money(Decimal(str(item["mass_g"])) / 1000 * 25 * Decimal("1.25"))
            notes = "FFF PETG; CAD solid upper-bound mass x25USD/kg x1.25 waste; machine time and labor excluded"
        else:
            if number not in ALLOWANCES: raise ValueError(f"Unpriced CAD part: {number}")
            kind, unit, notes = ALLOWANCES[number]; description = item["name"]
        rows.append(dict(zip(fields, [number, description, kind, count, item["material"],
            money(unit), money(Decimal(unit)*count), ";".join(i["id"] for i in items), ref, notes])))
    for ref, entry in sorted(electrical.items()):
        if ref in used_electrical: continue
        count = int(entry["quantity"]); unit = entry["estimated_unit_USD"]
        rows.append(dict(zip(fields, ["NODI-"+ref, entry["description"], "buy", count,
            entry["manufacturer_or_requirement"], money(unit), money(Decimal(unit)*count),
            "not modeled - electrical accessory", ref, entry["status"]])))
    rows.append(dict(zip(fields, ["NODI-A01", "Cable grommets and mechanical strain-relief kit", "buy", 1,
        "Elastomer grommets plus insulated cable clamps", "2.00", "2.00", "not modeled - harness accessory", "",
        "Fit rear7.2mm entry and deck10mm bore with approximately6mm freeID; head8mm edge protection; three nylon ties for inlet plus both moving-harness ends; supplier selection and cable pull test open"])))
    output = io.StringIO(newline=""); writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    total = sum(Decimal(row["estimated_extended_USD"]) for row in rows)
    # Every nonvisual CAD instance maps once, and each electrical purchase maps once.
    covered = [ident for row in rows for ident in row["cad_instance_ids"].split(";")
               if ident and not ident.startswith("not modeled")]
    expected = [i["id"] for i in manifest["instances"] if i["part_number"] != "VISUAL"]
    assert sorted(covered) == sorted(expected), "Unmapped or duplicated CAD instances"
    assert len([r for r in rows if r["electronics_ref"]]) == len(electrical)
    electrical_total = sum(Decimal(r["estimated_extended_USD"]) for r in rows if r["electronics_ref"])
    assert electrical_total == Decimal("84.65"), "Electrical costs changed; update documented subtotal"
    return output.getvalue(), len(rows), len(covered), total

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); content, rows, covered, total = render_bom()
    destination = ROOT / "Manufacturing/BOM.csv"
    if args.check:
        if not destination.exists() or destination.read_text() != content:
            raise SystemExit("BOM differs from current CAD/electrical inputs; run Manufacturing/build_bom.py")
        print(f"PASS: {rows} BOM rows map {covered} nonvisual CAD instances once; electrical subtotal 84.65 USD; total {total} USD")
    else:
        destination.write_text(content)
        print(f"Wrote {rows} rows; {covered} nonvisual CAD instances; total planning allowance {total}USD")
