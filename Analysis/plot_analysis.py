#!/usr/bin/env python3
"""Create standalone engineering figures from the executed calculation outputs."""
from pathlib import Path
import csv
import json
import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "nodi-matplotlib-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
r = json.loads((HERE / "analysis_results.json").read_text())
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "savefig.facecolor": "white"})

fig, ax = plt.subplots(figsize=(8.0, 3.8), constrained_layout=True)
values = [r["motor"]["pitch_factored_required_Nm"],
          r["motor"]["yaw_factored_required_Nm"],
          r["motor"]["assumed_operating_budget_Nm"]]
bars = ax.barh(["Pitch demand (SF = 2)", "Yaw demand (SF = 2)", "Assumed operating budget"],
               values, color=["#da7443", "#416879", "#486548"], height=0.55)
ax.invert_yaxis()
ax.bar_label(bars, labels=[f" {v:.4f} N·m" for v in values], padding=3)
ax.set(xlim=(0, max(values)*1.32), xlabel="Torque [N·m]",
       title="Actuator sizing — analytical screening")
ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)
fig.text(0.02, -0.14,
         "Budget = 25% of MG90S 4.8 V stall torque; designer assumption, not a continuous rating.\n"
         "CAD mass +25%, 5 g head wiring, 10 mm CG offset, 180°/s². No hardware test.",
         fontsize=8)
fig.savefig(ROOT / "Images" / "actuator_torque_analysis.png", dpi=220, bbox_inches="tight")
fig.savefig(HERE / "actuator_torque_analysis.pdf", bbox_inches="tight")
plt.close(fig)

samples=list(csv.DictReader((HERE/"motion_profile.csv").open()))
fig, axes=plt.subplots(3,1,figsize=(8.0,6.0),sharex=True,constrained_layout=True)
for axis,color in [("pitch","#da7443"),("yaw","#416879")]:
    data=[row for row in samples if row["axis"]==axis]
    t=[float(row["time_s"]) for row in data]
    for ax,key in zip(axes,["angle_deg","velocity_deg_s","acceleration_deg_s2"]):
        ax.plot(t,[float(row[key]) for row in data],label=axis.capitalize(),color=color,lw=2)
for ax,label in zip(axes,["Angle [°]","Velocity [°/s]","Acceleration [°/s²]"]):
    ax.set_ylabel(label);ax.grid(alpha=0.2)
axes[0].set_title("Full-travel quintic command profiles — calculated")
axes[0].legend(loc="best",frameon=False,ncol=2)
axes[1].axhline(60,color="#777777",lw=1,ls="--")
axes[2].axhline(180,color="#777777",lw=1,ls="--")
axes[2].axhline(-180,color="#777777",lw=1,ls="--")
axes[-1].set_xlabel("Time [s]")
fig.text(0.02,-0.025,"Command trajectories only. Loaded servo position, speed, backlash and current remain unmeasured.",fontsize=8)
fig.savefig(ROOT / "Images" / "command_motion_profiles.png",dpi=220,bbox_inches="tight")
fig.savefig(HERE / "command_motion_profiles.pdf",bbox_inches="tight")
plt.close(fig)
print("Created Images/actuator_torque_analysis.png and Images/command_motion_profiles.png with PDF copies in Analysis/")
