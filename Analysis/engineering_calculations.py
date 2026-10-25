#!/usr/bin/env python3
"""Reproduce NODI screening calculations using actual generated CAD mass properties.

Run from any directory: python Analysis/engineering_calculations.py
No third-party Python dependencies. Fails if the real CAD manifest is absent.
Outputs analysis_results.json, engineering_analysis.md, and motion_profile.csv.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
Q1_MAX = 1.875
Q2_MAX = 10.0 / math.sqrt(3.0)


def mass_kg(items):
    return sum(float(p["mass_g"]) for p in items) / 1000.0


def center_of_mass(items):
    total = mass_kg(items)
    if total <= 0:
        raise ValueError("Moving assembly must have positive mass")
    return [sum(float(p["mass_g"]) * float(p["com_mm"][i]) for p in items)
            / (1000.0 * total) for i in range(3)]


def bbox_inertia_upper_bound(items, axis, origin_mm):
    # Put all mass at the farthest bounding-box corner in the normal plane.
    # This is deliberately more conservative than assuming uniform solid boxes.
    normal = [i for i in range(3) if i != axis]
    value = 0.0
    for p in items:
        maximum_radius_squared = sum(
            max(abs(float(p["bbox_mm"]["min"][i]) - origin_mm[i]),
                abs(float(p["bbox_mm"]["max"][i]) - origin_mm[i])) ** 2
            for i in normal) * 1e-6
        value += float(p["mass_g"]) / 1000.0 * maximum_radius_squared
    return value


def trajectory(distance_deg, motion):
    duration = max(motion["minimum_duration_s"],
                   Q1_MAX * distance_deg / motion["max_speed_deg_s"],
                   math.sqrt(Q2_MAX * distance_deg / motion["max_acceleration_deg_s2"]))
    return {"distance_deg": distance_deg, "duration_s": duration,
            "peak_speed_deg_s": Q1_MAX * distance_deg / duration,
            "peak_acceleration_deg_s2": Q2_MAX * distance_deg / duration ** 2}


def main():
    inputs_path = HERE / "analysis_inputs.json"
    inp = json.loads(inputs_path.read_text())
    manifest_path = ROOT / inp["cad_manifest"]
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Regenerate actual CAD first; missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    parameters_path = ROOT / inp["cad_parameters"]
    parameters = json.loads(parameters_path.read_text())
    parts = manifest["instances"]
    mechanism = manifest["mechanism"]
    pitch_parts = [p for p in parts if p["group"] == "pitch"]
    yaw_parts = [p for p in parts if p["group"] == "yaw"]
    if not pitch_parts or not yaw_parts:
        raise ValueError("CAD manifest requires identified pitch and yaw subassemblies")
    # Guard duplicated inspection assumptions against stale CAD revisions.
    shared = [(inp["fits"]["head_width_mm"], parameters["head_width_mm"], "head width"),
              (inp["fits"]["yoke_inner_gap_mm"], parameters["yoke_gap_mm"], "yoke gap"),
              (inp["fits"]["pan_pilot_nominal_diameter_mm"], parameters["pilot_diameter_mm"], "pan pilot"),
              (inp["fits"]["pan_bore_nominal_diameter_mm"], parameters["lid_bearing_bore_mm"], "pan bore"),
              (inp["structure"]["yoke_arm_thickness_x_mm"], parameters["yoke_thickness_mm"], "arm thickness"),
              (inp["structure"]["yoke_arm_depth_y_mm"], parameters["yoke_arm_depth_mm"], "arm depth"),
              (inp["structure"]["yoke_arm_free_length_mm"], parameters["pitch_axis_height_mm"] - parameters["pan_plate_bottom_mm"] - parameters["pan_plate_thickness_mm"], "arm free length")]
    shared += list(zip(inp["thermal_and_power"]["base_dimensions_mm"],
                       [parameters[k] for k in ("base_width_mm", "base_depth_mm", "base_height_mm")],
                       ["base width", "base depth", "base height"]))
    for analysis_value, cad_value, name in shared:
        if abs(analysis_value - cad_value) > 1e-8:
            raise ValueError(f"Stale analysis {name}: {analysis_value} vs CAD {cad_value}; review/update inputs")
    feet = [p for p in parts if p["id"].startswith("foot_")]
    if len(feet) != inp["structure"]["foot_count"]:
        raise ValueError("Foot count differs from analysis inputs")
    for foot in feet:
        if abs((foot["bbox_mm"]["max"][0] - foot["bbox_mm"]["min"][0]) - inp["structure"]["foot_diameter_mm"]) > 1e-8:
            raise ValueError("Foot diameter differs from analysis inputs")
    actual_support_halfspan_y = min(max(p["bbox_mm"]["max"][1] for p in feet),
                                    -min(p["bbox_mm"]["min"][1] for p in feet))
    if inp["structure"]["minimum_foot_support_halfspan_y_mm"] > actual_support_halfspan_y:
        raise ValueError("Assumed foot support polygon exceeds actual CAD geometry")
    for part in parts:
        if float(part["mass_g"]) < 0:
            raise ValueError(f"Negative mass: {part['id']}")
    g = inp["gravity_m_s2"]
    a = inp["actuator"]
    m = inp["motion"]
    s = inp["structure"]
    stability = inp["stability"]
    pitch_axis = mechanism["pitch_axis_mm"]
    yaw_axis = mechanism["yaw_axis_mm"]
    head_mass = mass_kg(pitch_parts)
    yaw_mass = mass_kg(yaw_parts)
    total_mass = mass_kg(parts)
    head_com = center_of_mass(pitch_parts)
    total_com = center_of_mass(parts)
    mass_factor = 1 + inp["mass_uncertainty_fraction"]
    head_design_mass = head_mass * mass_factor + inp["unmodeled_head_wiring_mass_kg"]
    yaw_design_mass = (head_mass + yaw_mass) * mass_factor + inp["unmodeled_head_wiring_mass_kg"]
    total_design_mass = total_mass * mass_factor + inp["unmodeled_head_wiring_mass_kg"] + inp["unmodeled_fixed_wiring_mass_kg"]
    head_radius = math.hypot(head_com[1] - pitch_axis[1], head_com[2] - pitch_axis[2]) / 1000.0
    cg_offset = max(inp["minimum_head_cg_offset_budget_mm"] / 1000.0,
                    head_radius + inp["head_cg_uncertainty_mm"] / 1000.0)
    pitch_I = bbox_inertia_upper_bound(pitch_parts, 0, pitch_axis)
    # Add 5 g wiring at the outside head corner and increase all CAD inertia by 25%.
    head_sphere_r2 = max(sum(max(abs(p["bbox_mm"]["min"][i] - pitch_axis[i]),
                                abs(p["bbox_mm"]["max"][i] - pitch_axis[i])) ** 2
                           for i in range(3)) for p in pitch_parts) * 1e-6
    pitch_I = mass_factor * pitch_I + inp["unmodeled_head_wiring_mass_kg"] * head_sphere_r2
    # Sphere about the pitch axis bounds all tilted head poses about coaxial yaw.
    # CAD pitch axis x,y must lie on yaw axis for this simplified bound.
    if any(abs(pitch_axis[i] - yaw_axis[i]) > 1e-8 for i in (0, 1)):
        raise ValueError("Update yaw-inertia bound for offset axes")
    yaw_I = head_design_mass * head_sphere_r2 + mass_factor * bbox_inertia_upper_bound(yaw_parts, 2, yaw_axis)
    acceleration = math.radians(m["max_acceleration_deg_s2"])
    omega = math.radians(m["max_speed_deg_s"])
    stall = a["stall_torque_kgf_cm_at_4_8V"] * g * 0.01
    operating = stall * a["assumed_operating_fraction_of_stall"]
    pitch_gravity = head_design_mass * g * cg_offset
    pitch_inertial = pitch_I * acceleration
    pitch_unfactored = pitch_gravity + pitch_inertial + a["pitch_joint_friction_Nm"] + a["pitch_cable_drag_Nm"]
    pitch_demand = a["torque_safety_factor"] * pitch_unfactored
    yaw_inertial = yaw_I * acceleration
    yaw_unfactored = yaw_inertial + a["yaw_joint_friction_Nm"] + a["yaw_cable_drag_Nm"]
    yaw_demand = a["torque_safety_factor"] * yaw_unfactored
    washer_outer = parameters["washer_od_mm"] / 2000.0
    washer_inner = parameters["washer_id_mm"] / 2000.0
    washer_effective_radius = (2.0/3.0) * (washer_outer**3 - washer_inner**3) / (washer_outer**2 - washer_inner**2)
    yaw_thrust_friction_estimate = a["assumed_thrust_washer_friction_coefficient"] * yaw_design_mass * g * washer_effective_radius
    pitch_trajectory = trajectory(mechanism["pitch_limits_deg"][1] - mechanism["pitch_limits_deg"][0], m)
    yaw_trajectory = trajectory(mechanism["yaw_limits_deg"][1] - mechanism["yaw_limits_deg"][0], m)

    # Yoke arm: vertical load is axial; eccentricity/pitch moment bends in YZ.
    L = s["yoke_arm_free_length_mm"] / 1000.0
    b = s["yoke_arm_thickness_x_mm"] / 1000.0
    d = s["yoke_arm_depth_y_mm"] / 1000.0
    E = s["youngs_modulus_Pa"]
    I_strong, I_weak = b*d**3/12.0, d*b**3/12.0
    axial_force = s["proof_vertical_load_factor"] * head_design_mass * g / s["yoke_arm_count"]
    # All conservative pitch demand on a single driven arm; no sharing assumed.
    pitch_arm_moment = s["proof_vertical_load_factor"] * pitch_gravity + a["torque_safety_factor"] * (pitch_inertial + a["pitch_joint_friction_Nm"] + a["pitch_cable_drag_Nm"])
    axial_stress = axial_force / (b*d)
    bending_stress = pitch_arm_moment * (d/2.0) / I_strong
    strong_deflection = pitch_arm_moment * L**2 / (2.0 * E * I_strong)
    axial_deflection = axial_force * L / (E*b*d)
    # Head CG radial bound gives translational inertial force from yaw and pitch.
    cg_radius_for_reaction = max(cg_offset, math.sqrt(head_sphere_r2))
    transverse_force = head_design_mass * cg_radius_for_reaction * (acceleration + omega**2) / s["yoke_arm_count"]
    weak_bending_stress = transverse_force * L * (b/2.0) / I_weak
    weak_deflection = transverse_force * L**3 / (3.0 * E * I_weak)
    combined_stress = axial_stress + bending_stress + weak_bending_stress
    max_deflection = strong_deflection + weak_deflection + axial_deflection
    fastener_d = s["pivot_nominal_diameter_mm"] / 1000.0
    pivot_force = math.hypot(axial_force, transverse_force)
    pivot_shear = pivot_force / (math.pi * fastener_d**2 / 4.0)
    pivot_bearing = pivot_force / (fastener_d*b)
    boss_area = math.pi/4 * ((s["base_boss_outer_diameter_mm"]/1000)**2 - (s["base_boss_hole_diameter_mm"]/1000)**2)
    boss_stress = s["proof_vertical_load_factor"] * total_design_mass * g / s["base_cover_screws"] / boss_area
    foot_pressure = total_design_mass * g / (s["foot_count"] * math.pi * (s["foot_diameter_mm"] / 2000.0)**2)
    # Main enclosure: average wall load and a deliberately simple lid beam surrogate.
    # The lid's actual plate/contact boundary conditions require prototype/FEA review.
    wall_t = parameters["wall_mm"] / 1000.0
    wall_area = 2*(parameters["base_width_mm"] + parameters["base_depth_mm"]) / 1000.0 * wall_t
    wall_stress = s["proof_vertical_load_factor"] * total_design_mass * g / wall_area
    deck_span = (parameters["base_depth_mm"] - 2*parameters["wall_mm"]) / 1000.0
    deck_effective_width = (parameters["base_width_mm"] - parameters["lid_bearing_bore_mm"]) / 1000.0
    deck_I = deck_effective_width * wall_t**3 / 12
    deck_proof_force = s["proof_vertical_load_factor"] * yaw_design_mass * g
    deck_beam_stress = (deck_proof_force*deck_span/4) * (wall_t/2) / deck_I
    deck_beam_deflection = deck_proof_force*deck_span**3 / (48*E*deck_I)
    arm_spring_rate = 3 * E * I_weak / L**3
    ideal_mode_hz = math.sqrt(s["yoke_arm_count"] * arm_spring_rate / head_design_mass) / (2*math.pi)
    stop_energy = 0.5 * pitch_I * omega**2
    stop_angle = math.radians(m["stop_compliance_deg"])
    stop_inertial_torque = stop_energy / stop_angle
    stop_average_force = (stop_inertial_torque + stall) / (m["stop_effective_radius_mm"] / 1000.0)

    # Minimum restoring weight prevents an added mass margin from creating a false pass.
    min_mass = total_mass * stability["minimum_static_mass_fraction"]
    support_halfspan = s["minimum_foot_support_halfspan_y_mm"] / 1000.0
    # Bound whole CG shift if the head's full budget eccentricity moves toward the edge.
    cg_offset_y = abs(total_com[1]) / 1000.0 + head_design_mass * cg_offset / max(min_mass, 1e-9)
    cg_height = max(total_com[2]/1000.0, 0.060)  # floor avoids optimistic low CG from simplified parts.
    lever = support_halfspan - cg_offset_y
    tip_angle_deg = math.degrees(math.atan2(lever, cg_height))
    restoring = min_mass * g * lever
    inertial_horizontal = yaw_design_mass * cg_radius_for_reaction * (acceleration + omega**2)
    # Whole-device balance: gravity is already included in the shifted total CG.
    # Add only inertial moment and angular acceleration; internal motor/cable
    # reactions must not double-count the head's gravitational moment.
    dynamic_overturn = inertial_horizontal * pitch_axis[2]/1000.0 + pitch_inertial
    push_moment = stability["horizontal_push_N"] * stability["push_height_mm"] / 1000.0
    minimum_mass_for_push = (push_moment + dynamic_overturn + head_design_mass*g*cg_offset) / (g * (support_halfspan - abs(total_com[1])/1000.0))
    sliding_force = stability["assumed_foot_static_friction_coefficient"] * min_mass * g
    sliding_demand = stability["horizontal_push_N"] + inertial_horizontal

    f = inp["fits"]
    t = f["printed_linear_tolerance_mm"]
    side_total = f["yoke_inner_gap_mm"] - f["head_width_mm"]
    side_total_min = side_total - 2*t
    leftover_after_washer = side_total_min - f["left_pivot_washer_thickness_mm"] - f["washer_thickness_tolerance_mm"]
    pilot_nominal = f["pan_bore_nominal_diameter_mm"] - f["pan_pilot_nominal_diameter_mm"]
    pilot_min = pilot_nominal - 2*t
    pilot_finished_min = pilot_nominal + f["finished_bore_lower_tolerance_mm"] - f["finished_pilot_upper_tolerance_mm"]
    screw_hole_min = f["m3_clearance_hole_mm"] - t - f["m3_max_nominal_diameter_mm"]
    carrier_hole_min = f["m3_carrier_clearance_hole_mm"] - t - f["m3_max_nominal_diameter_mm"]
    carrier_finished_min = f["m3_carrier_clearance_hole_mm"] + f["finished_carrier_hole_lower_tolerance_mm"] - f["m3_max_nominal_diameter_mm"]

    h = inp["thermal_and_power"]
    x,y,z = [v/1000.0 for v in h["base_dimensions_mm"]]
    exposed = (x*y + 2*(x*z+y*z)) * h["effective_exposed_area_fraction"]
    heat = h["logic_display_alarm_average_heat_W"] + 2*h["average_servo_heat_each_W"]
    hot = h["ambient_C"] + heat / (h["h_effective_low_W_m2K"] * exposed)
    cool = h["ambient_C"] + heat / (h["h_effective_high_W_m2K"] * exposed)
    current = h["logic_peak_input_current_A"] + 2*h["assumed_servo_stall_current_each_A"]
    droop = h["illustrative_transient_A"] * h["illustrative_transient_s"] / h["bulk_capacitance_F"]
    weights = [0.40,0.10,0.08,0.05,0.07,0.05,0.10,0.15]
    scores = {"A_pan_tilt":[5,3,4,3,3,3,4,4],"B_single_nod":[3,5,5,4,4,4,4,5],"C_eyelids":[3,3,3,3,3,2,4,3]}
    weighted = {name:sum(w*v for w,v in zip(weights, score)) for name,score in scores.items()}
    checks = {
        "pitch_torque_within_assumed_operating_budget": pitch_demand <= operating,
        "yaw_torque_within_assumed_operating_budget": yaw_demand <= operating,
        "yaw_washer_friction_estimate_within_allowance": yaw_thrust_friction_estimate <= a["yaw_joint_friction_Nm"],
        "mass_budget_below_0_50kg": total_design_mass <= 0.50,
        "arm_stress_below_screening_allowable": combined_stress <= s["screening_allowable_Pa"],
        "arm_displacement_below_0_5mm": max_deflection*1000 <= s["arm_tip_displacement_limit_mm"],
        "static_tip_angle_at_least_10deg": tip_angle_deg >= stability["minimum_tip_angle_deg"],
        "one_newton_push_tip_screen": restoring >= push_moment + dynamic_overturn,
        "one_newton_push_sliding_screen_with_assumed_friction": sliding_force >= sliding_demand,
        "pan_pilot_has_positive_worst_case_clearance_as_printed": pilot_min > 1e-8,
        "pan_pilot_has_positive_clearance_after_specified_finishing": pilot_finished_min > 1e-8,
        "carrier_holes_have_positive_worst_case_clearance_as_printed": carrier_hole_min > 1e-8,
        "carrier_holes_have_positive_clearance_after_specified_finishing": carrier_finished_min > 1e-8,
        "thermal_low_h_below_surface_target": hot <= h["surface_target_C"],
        "assumed_peak_current_below_supply_rating": current <= h["proposed_supply_rating_A"]
    }
    out = {
        "evidence_type": "Analytical screening; no physical test or FEA",
        "input_revision":inp["revision"],
        "cad_manifest_sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "cad_parameters_sha256":hashlib.sha256(parameters_path.read_bytes()).hexdigest(),
        "analysis_inputs_sha256":hashlib.sha256(inputs_path.read_bytes()).hexdigest(),
        "shared_cad_dimensions_checked": [item[2] for item in shared] + ["foot count", "foot diameter", "foot support half-span"],
        "cad_parts": {"total_count":len(parts), "pitch_ids":[p["id"] for p in pitch_parts], "yaw_ids":[p["id"] for p in yaw_parts]},
        "mass": {"cad_total_kg":total_mass,"cad_head_kg":head_mass,"cad_yaw_only_kg":yaw_mass,"head_design_budget_kg":head_design_mass,"yaw_design_budget_kg":yaw_design_mass,"total_design_budget_kg":total_design_mass,"head_cad_com_mm":head_com,"total_cad_com_mm":total_com,"head_cad_cg_radius_mm":1000*head_radius,"head_design_cg_offset_mm":1000*cg_offset},
        "motor": {"stall_torque_Nm":stall,"assumed_operating_budget_Nm":operating,"pitch_gravity_Nm":pitch_gravity,"pitch_inertia_upper_bound_kg_m2":pitch_I,"pitch_inertial_Nm":pitch_inertial,"pitch_unfactored_Nm":pitch_unfactored,"pitch_factored_required_Nm":pitch_demand,"pitch_budget_reserve_ratio":operating/pitch_demand,"yaw_inertia_upper_bound_kg_m2":yaw_I,"yaw_inertial_Nm":yaw_inertial,"yaw_unfactored_Nm":yaw_unfactored,"yaw_factored_required_Nm":yaw_demand,"yaw_budget_reserve_ratio":operating/yaw_demand,"yaw_thrust_friction_estimate_Nm":yaw_thrust_friction_estimate,"yaw_washer_effective_radius_mm":washer_effective_radius*1000},
        "motion": {"pitch_full_travel":pitch_trajectory,"yaw_full_travel":yaw_trajectory},
        "structure": {"vertical_proof_force_each_arm_N":axial_force,"driven_arm_pitch_moment_Nm":pitch_arm_moment,"axial_stress_MPa":axial_stress/1e6,"pitch_bending_stress_MPa":bending_stress/1e6,"lateral_dynamic_bending_stress_MPa":weak_bending_stress/1e6,"combined_screen_stress_MPa":combined_stress/1e6,"screening_allowable_MPa":s["screening_allowable_Pa"]/1e6,"screening_margin":s["screening_allowable_Pa"]/combined_stress,"combined_arm_deflection_mm":1000*max_deflection,"pivot_shear_MPa":pivot_shear/1e6,"printed_pivot_bearing_MPa":pivot_bearing/1e6,"base_boss_average_bearing_MPa":boss_stress/1e6,"foot_contact_pressure_MPa":foot_pressure/1e6,"main_wall_average_stress_MPa":wall_stress/1e6,"deck_beam_surrogate_3g_load_N":deck_proof_force,"deck_beam_surrogate_3g_stress_MPa":deck_beam_stress/1e6,"deck_beam_surrogate_3g_deflection_mm":1000*deck_beam_deflection,"deck_beam_surrogate_1g_deflection_mm":1000*deck_beam_deflection/s["proof_vertical_load_factor"],"idealized_arm_bending_mode_Hz":ideal_mode_hz},
        "dynamics": {"pitch_stop_kinetic_energy_J":stop_energy,"stop_average_inertial_torque_Nm":stop_inertial_torque,"stop_average_force_including_stall_N":stop_average_force,"horizontal_inertial_reaction_N":inertial_horizontal,"dynamic_overturning_moment_Nm":dynamic_overturn},
        "stability": {"minimum_total_mass_kg":min_mass,"minimum_mass_for_push_at_assumed_CAD_cg_kg":minimum_mass_for_push,"conservative_cg_height_mm":cg_height*1000,"conservative_cg_y_offset_mm":cg_offset_y*1000,"support_lever_mm":lever*1000,"static_tip_angle_deg":tip_angle_deg,"restoring_moment_Nm":restoring,"one_newton_push_moment_Nm":push_moment,"push_with_dynamic_margin_ratio":restoring/(push_moment+dynamic_overturn),"assumed_sliding_threshold_N":sliding_force,"push_plus_inertia_horizontal_force_N":sliding_demand,"assumed_sliding_reserve_ratio":sliding_force/sliding_demand},
        "tolerance": {"head_yoke_total_nominal_gap_mm":side_total,"head_yoke_total_worst_gap_mm":side_total_min,"head_yoke_worst_gap_after_one_washer_mm":leftover_after_washer,"pan_pilot_nominal_diametral_clearance_mm":pilot_nominal,"pan_pilot_worst_as_printed_clearance_mm":pilot_min,"pan_pilot_finished_minimum_clearance_mm":pilot_finished_min,"m3_minimum_diametral_hole_clearance_mm":screw_hole_min,"m3_carrier_worst_as_printed_clearance_mm":carrier_hole_min,"m3_carrier_finished_minimum_clearance_mm":carrier_finished_min},
        "thermal_and_power": {"estimated_heat_W":heat,"effective_exposed_area_m2":exposed,"estimated_surface_low_C":cool,"estimated_surface_high_C":hot,"assumed_peak_current_A":current,"supply_current_reserve_A":h["proposed_supply_rating_A"]-current,"illustrative_capacitor_only_voltage_droop_V":droop},
        "decision_matrix": {"weights":weights,"scores":scores,"weighted_scores":weighted,"equal_weight_scores":{name:sum(score)/len(score) for name,score in scores.items()},"expressiveness_weight_transfer_to_simplicity_for_A_B_tie":(weighted["A_pan_tilt"]-weighted["B_single_nod"])/4},
        "analytical_checks_only":checks,
        "limitations":["No physical test, FEA, creep, fatigue, servo continuous-rating, thermal, acoustic or electrical validation.","Bounding-box inertia and assumed mass/CG margins are screens; replace them with measured prototype properties.","Motor stall torque is not safe continuous torque. Reserve ratio compares to an assumed 25%-stall operating budget.","A failed screen is retained in this record and requires finishing, redesign or a physical test before acceptance."]
    }
    (HERE/"analysis_results.json").write_text(json.dumps(out,indent=2)+"\n")
    with (HERE/"motion_profile.csv").open("w",newline="") as stream:
        writer=csv.writer(stream)
        writer.writerow(["axis","time_s","angle_deg","velocity_deg_s","acceleration_deg_s2"])
        for axis,traj,limits in [("pitch",pitch_trajectory,mechanism["pitch_limits_deg"]),("yaw",yaw_trajectory,mechanism["yaw_limits_deg"])]:
            for k in range(201):
                u=k/200; T=traj["duration_s"]; distance=traj["distance_deg"]
                q=10*u**3-15*u**4+6*u**5
                dq=30*u**2-60*u**3+30*u**4
                ddq=60*u-180*u**2+120*u**3
                writer.writerow([axis,f"{u*T:.6f}",f"{limits[0]+distance*q:.6f}",f"{distance*dq/T:.6f}",f"{distance*ddq/T**2:.6f}"])
    write_markdown(out,inp)
    print(json.dumps({"output":"Analysis/analysis_results.json","cad_total_kg":total_mass,"pitch_required_Nm":pitch_demand,"yaw_required_Nm":yaw_demand,"checks":checks},indent=2))


def write_markdown(r,i):
    mass,motor,st,dy,tip,fit,heat = [r[k] for k in ("mass","motor","structure","dynamics","stability","tolerance","thermal_and_power")]
    rows="\n".join(f"| {key.replace('_',' ')} | {'PASS within stated model' if value else 'OPEN / model does not demonstrate target'} |" for key,value in r["analytical_checks_only"].items())
    text=f"""# Engineering analysis — revision {i['revision']}

**Calculated screening results, not experimental validation.** Reproduce with `python Analysis/engineering_calculations.py` after CAD generation. Numeric inputs are in [analysis_inputs.json](analysis_inputs.json); complete outputs are in [analysis_results.json](analysis_results.json). The script reads the actual [CAD manifest](../CAD/manifest.json), records its SHA-256, and derives moving groups from instance membership. No finite-element solver was successfully run; no FEA results are claimed.

## Mass, actuator and geometry basis

| Quantity | Value | Basis |
|---|---:|---|
| CAD assembly mass | {mass['cad_total_kg']*1000:.1f} g | Solid volume × stated density; purchased-component overrides |
| CAD pitch group mass | {mass['cad_head_kg']*1000:.1f} g | Includes the head, display and moving tilt servo |
| Head design mass | {mass['head_design_budget_kg']*1000:.1f} g | CAD ×1.25 + 5 g cable allowance |
| Total design mass budget | {mass['total_design_budget_kg']*1000:.1f} g | CAD ×1.25 + 20 g unmodeled wiring allowance |
| Head CAD CG radius from pitch axis | {mass['head_cad_cg_radius_mm']:.2f} mm | Mass-weighted CAD component centers |
| Design CG offset | {mass['head_design_cg_offset_mm']:.2f} mm | Maximum of CAD radius +5 mm and 10 mm minimum |
| MG90S stall torque at 4.8 V | {motor['stall_torque_Nm']:.5f} N·m | Manufacturer 1.8 kgf·cm; conversion 1 kgf·cm = 0.0980665 N·m |
| Assumed operating budget | {motor['assumed_operating_budget_Nm']:.5f} N·m | Designer-selected 25% of stall, not a continuous rating |

The [source register](sources.md) identifies the manufacturer data and their limitations. Printed PETG density is 1.27 g/cm³. Calculations use reduced modulus **1.0 GPa** and a **10 MPa** stress screening allowable. Neither is a material certificate; interlayer strength, creep and manufacturing variation remain prototype risks. Purchased masses and modeled centers are nominal envelopes, not measured parts.

## Motor sizing and motion

Pitch: `T_required = SF × (m g e + I α + T_friction + T_cable)`, with SF=2, friction=0.003 N·m and cable drag=0.002 N·m. Gravity uses the full design offset in its worst orientation. Inertia is bounded by placing each part's mass at the farthest corner of its actual bounding box in the rotation plane, then applying the mass margin. This avoids an optimistic uniform-box approximation.

| Pitch torque term | N·m |
|---|---:|
| Gravity | {motor['pitch_gravity_Nm']:.5f} |
| Inertia at 180°/s² | {motor['pitch_inertial_Nm']:.5f} |
| Friction + cable allowance | 0.00500 |
| Required including SF=2 | **{motor['pitch_factored_required_Nm']:.5f}** |
| Assumed operating budget / required | **{motor['pitch_budget_reserve_ratio']:.2f}** |

Yaw has no intended gravity term about a vertical axis. Its inertia bound includes the whole tilted head in a bounding sphere plus the yaw platform. `T_yaw = 2 × (I α + 0.003 + 0.002)` = **{motor['yaw_factored_required_Nm']:.5f} N·m**, with budget reserve **{motor['yaw_budget_reserve_ratio']:.2f}**. Desk inclination, binding, harness drag and servo gear friction can invalidate this allowance. Measure current and cable torque at the travel corners before increasing duty.

For the Ø40/25 mm annular thrust washer, uniform-pressure effective radius is `R_eff=(2/3)(R_o³−R_i³)/(R_o²−R_i²)` = {motor['yaw_washer_effective_radius_mm']:.2f} mm. A **purely assumed** dry friction coefficient μ=0.10 gives `T≈μ m g R_eff` = {motor['yaw_thrust_friction_estimate_Nm']:.5f} N·m, consistent with the 0.003 N·m allowance but leaving little friction margin. Surface finish, preload, contamination and pilot rubbing can increase this. The 0.002 N·m cable-drag allowance corresponds to only 0.10 N tangential force at a 20 mm lever; measure it with a spring scale or torque fixture at combined travel limits.

Stall torque is the zero-speed maximum from the vendor. It is not a safe holding or running rating. The no-load transit speed is about 600°/s; loaded speed under the required torque is not specified. The commanded 60°/s ceiling is deliberately much slower, but that comparison does not validate loaded tracking or life.

Firmware and this analysis use `q(u)=10u³−15u⁴+6u⁵`, with zero endpoint speed and acceleration. `max|q'|=1.875` and `max|q''|=10/√3`; choose `T=max(0.5,1.875 Δθ/60,√((10/√3) Δθ/180))` in seconds/degrees. Full pitch travel takes **{r['motion']['pitch_full_travel']['duration_s']:.3f} s**, full yaw **{r['motion']['yaw_full_travel']['duration_s']:.3f} s**. The [sampled profile](motion_profile.csv) is a calculated command trajectory, not a measured response.

## Structural load path

Head → servo horn/opposite pivot → two yoke arms → yaw platform → thrust washer/pilot → base lid → shell/feet. The servo horn transmits drive torque; the washer and opposite pivot are intended to relieve external cantilever loading on servo shafts. Contact, horn spline fit, screw engagement and actual load sharing require bench confirmation.

The yoke arm is idealized as a cantilever of free length 50 mm, section 4 mm in X ×12 mm in Y. Vertical **3 g** head load is axial; it is not treated as an arbitrary horizontal shock. Pitch reaction bends the arm in its stiffer plane, with the full drive moment assigned to one arm. `I_strong=b d³/12`, `I_weak=d b³/12`, `σ=F/A+Mc/I`, `δ_M=M L²/(2 E I)`, `δ_F=F L³/(3 E I)`. Lateral load includes tangential `m r α` and centripetal `m r ω²` terms using a conservative CG radius.

| Structural screen | Result |
|---|---:|
| Vertical proof load per arm | {st['vertical_proof_force_each_arm_N']:.3f} N |
| Driven-arm pitch moment | {st['driven_arm_pitch_moment_Nm']:.5f} N·m |
| Combined axial + bending stress | **{st['combined_screen_stress_MPa']:.3f} MPa** |
| 10 MPa allowable / modeled stress | {st['screening_margin']:.1f} |
| Combined arm displacement | **{st['combined_arm_deflection_mm']:.3f} mm** |
| M3 pivot single-shear stress | {st['pivot_shear_MPa']:.3f} MPa |
| Printed pivot bearing stress | {st['printed_pivot_bearing_MPa']:.3f} MPa |
| Base screw-boss average vertical bearing | {st['base_boss_average_bearing_MPa']:.3f} MPa |
| Average four-foot contact pressure | {st['foot_contact_pressure_MPa']:.4f} MPa |
| Main shell average vertical wall stress at 3 g | {st['main_wall_average_stress_MPa']:.4f} MPa |

The main 2.4 mm deck is also screened as a simply supported beam surrogate: span 95.2 mm, effective width `120−24.4=95.6 mm` (the central bore removed over the whole span), central rotating-assembly proof load {st['deck_beam_surrogate_3g_load_N']:.2f} N. `σ=(F L/4)(t/2)/I` and `δ=F L³/(48 E I)` give **{st['deck_beam_surrogate_3g_stress_MPa']:.2f} MPa**, **{st['deck_beam_surrogate_3g_deflection_mm']:.2f} mm at 3 g**, and **{st['deck_beam_surrogate_1g_deflection_mm']:.2f} mm at normal 1 g**. This rough model omits two-dimensional plate action, counterbores, load distribution and the actual edge/fastener contacts, so it is not a validated displacement prediction or upper bound. It identifies deck compliance and pilot/horn rubbing as physical inspection priorities. The 0.5 mm displacement acceptance applies to the yoke arm; **the complete assembly has not demonstrated equivalent stiffness**. Increase deck ribbing/thickness or add a supported bearing bridge if measured movement changes running clearance.

Fastener calculations check external load only: `τ=F/(πd²/4)` and printed bearing `p=F/(d t)`. Bearing uses a conservative 3 mm projected diameter; the actual passive pivot includes a 4 mm sleeve. These checks do **not** establish thread pullout, insert retention, horn strength, preload or resistance to loosening. Boss calculation uses four effective 8 mm OD /3.4 mm ID net bearing sections, conservatively removing more material than the CAD Ø2.7 thread pilot. Inspect the actual boss load path. Do not torque polymer screws to metal-joint values. Use low assembly torque and mark/check fasteners during cycling.

The idealized weak-plane arm mode is **{st['idealized_arm_bending_mode_Hz']:.1f} Hz**, obtained from `k=3EI/L³` and `f=(1/2π)√(2k/m)`. This is not a modal FEA or measured resonance; joint compliance, servo control and plastic damping are omitted. Slow gestures avoid deliberate excitation near this estimate, but camera/accelerometer and acoustic checks remain necessary.

## Dynamics, tipping and stop fault

At the 60°/s ceiling the bounded pitch kinetic energy is **{dy['pitch_stop_kinetic_energy_J']:.6f} J**. If absorbed over an assumed 2° compliant stop travel, energy balance gives average inertial torque **{dy['stop_average_inertial_torque_Nm']:.5f} N·m**. Adding a stalled motor gives an average force of **{dy['stop_average_force_including_stall_N']:.2f} N** at the CAD's 12 mm pitch-stop radius. Peak force may be substantially higher. The current printed stop has no characterized compliant bumper, so the assumed 2° absorption must not be treated as a provided feature or guaranteed deflection. This is a **fault-load estimate**, not demonstrated stop survival. Printed stops are secondary travel protection; firmware limits must avoid contacting them.

Stability uses a minimum mass equal to **80%** of nominal CAD mass (not the heavy mass budget), a foot support half-span of {i['structure']['minimum_foot_support_halfspan_y_mm']:.0f} mm in Y, and whole-assembly CG offset enlarged by the head design eccentricity. CG height is at least 60 mm. Modeled restoring moment is **{tip['restoring_moment_Nm']:.4f} N·m**; horizontal dynamic reaction is **{dy['horizontal_inertial_reaction_N']:.3f} N**. Gravity is included once through the displaced whole-device CG; the added dynamic moment includes translational and rotational inertia, without double-counting internal servo/cable reaction torque. Predicted static tip angle is **{tip['static_tip_angle_deg']:.1f}°**. Restoring / (1 N push at 100 mm + dynamic moment) is **{tip['push_with_dynamic_margin_ratio']:.2f}**. These calculations omit table motion, an off-axis power cable pull and compliant feet. Measured tip, slip and impulse tests are required. Assumed foot friction μ=0.4 gives a sliding threshold of **{tip['assumed_sliding_threshold_N']:.2f} N**; the actual desk/foot pair can differ greatly.

**Mass acceptance gate:** The fully solid CAD polymer mass is not a measured lower bound; slicer infill can substantially reduce it. This result assumes an as-built stabilizing mass of at least **{math.ceil(tip['minimum_total_mass_kg']*1000)} g** and the stated CG bounds. Weigh the finished unit and verify CG/tilt before claiming that reserve. Solving the same level-desk moment balance gives a theoretical threshold of **{tip['minimum_mass_for_push_at_assumed_CAD_cg_kg']*1000:.0f} g** at the assumed CAD CG and head-offset allowance, but that threshold has no reserve and is not an acceptance substitute. If the unit is below the modeled mass floor, increase/retain ballast or rerun the balance with measured mass/CG; do not use the 490 g upper mass budget as stabilizing weight.

The assumed static sliding reserve is **{tip['assumed_sliding_reserve_ratio']:.2f}** against the 1 N push plus simultaneous horizontal inertia ({tip['push_plus_inertia_horizontal_force_N']:.3f} N). This is conditional on μ=0.4; force-gauge testing on the intended desk must establish actual friction. A tip calculation alone does not establish resistance to sliding.

## Fit and tolerance chains

| Interface | Nominal | Worst case with stated assumptions | Disposition |
|---|---:|---:|---|
| 88 mm yoke gap −86 mm head width | {fit['head_yoke_total_nominal_gap_mm']:.2f} mm total | {fit['head_yoke_total_worst_gap_mm']:.2f} mm total | Accounts for ±0.2 mm on each linear dimension |
| Above gap after one {i['fits']['left_pivot_washer_thickness_mm']:.1f}±0.1 mm washer | — | {fit['head_yoke_worst_gap_after_one_washer_mm']:.2f} mm remaining | Set axial retention with actual horn/pivot stack; this is not automatic equal side clearance |
| Ø24.4 bore −Ø24.0 pilot | {fit['pan_pilot_nominal_diametral_clearance_mm']:.2f} mm diametral | {fit['pan_pilot_worst_as_printed_clearance_mm']:.2f} mm | As-printed tolerance stack can consume all clearance; measure/finish the bore and pilot before operation |
| Finished bore Ø24.40 +0.20/−0 and pilot Ø24.00±0.10 | 0.40 mm diametral | {fit['pan_pilot_finished_minimum_clearance_mm']:.2f} mm | Drawing/process fit after controlled finishing and gauging; not an as-printed guarantee |
| Ø3.3 deck hole −M3 nominal screw | 0.30 mm diametral | {fit['m3_minimum_diametral_hole_clearance_mm']:.2f} mm | Deburr and gauge; position error is separate from size clearance |
| Ø3.2 carrier hole −M3 nominal screw | 0.20 mm diametral | {fit['m3_carrier_worst_as_printed_clearance_mm']:.2f} mm raw; {fit['m3_carrier_finished_minimum_clearance_mm']:.2f} mm after finishing | Ream/drill and gauge finished hole ≥3.20 mm; nominal printing alone can consume all clearance |

The pan pilot is an intentional unresolved process risk: use a calibration coupon, deburr and finish to a freely rotating measured fit. Simply printing the nominal CAD does not guarantee motion. Cable bend radius, vendor servo ear offsets, horn thickness and commercial-module tolerances require the assembly inspection. CAD collision checks do not include flexible cable shape or printed surface roughness.

## Thermal and power screen

Assumed dissipated heat is **{heat['estimated_heat_W']:.2f} W** (logic/display/alarm 0.8 W plus 0.25 W average heat per servo). For a 120×100×32 mm base, bottom excluded and 75% effective exposed area, `A={heat['effective_exposed_area_m2']:.5f} m²`. A lumped convection/radiation estimate `T_surface=T_ambient+P/(h_eff A)` at 30 °C gives **{heat['estimated_surface_low_C']:.1f}–{heat['estimated_surface_high_C']:.1f} °C** across `h_eff=10–4 W/m²K`. The low-transfer case can exceed the 45 °C target. Heat is spatially distributed, so this base-only lumped screen cannot predict servo winding or controller junction temperature. Actual power/duty and blocked-vent tests must resolve it.

Provisional peak-current budget is **{heat['assumed_peak_current_A']:.2f} A** ({i['thermal_and_power']['logic_peak_input_current_A']:.2f} A logic + two assumed 1.0 A stalled servos) against a proposed 5 V/3 A external supply, matching the electrical architecture. Manufacturer servo stall current is not specified. Use protected power distribution, common ground, decoupling and a current-limited first power-up; verify the actual servo supply stays within its rated range. A 1,000 µF capacitor alone supporting a 1 A transient for 1 ms would droop **{heat['illustrative_capacitor_only_voltage_droop_V']:.1f} V** by `ΔV=IΔt/C`: capacitance is not a substitute for a suitable supply, wiring and transient measurements.

## Numerical acceptance record

| Analytical check | Result |
|---|---|
{rows}

Every pass is conditional on the model assumptions. Open screens are deliberately retained. The [verification plan](../Documentation/requirements_and_verification.md) lists the required prototype tests, and [development roadmap](../Documentation/development_timeline.md) separates the one-day digital scope from commercial EVT/DVT/PVT.
"""
    (HERE/"engineering_analysis.md").write_text(text)


if __name__ == "__main__":
    main()
