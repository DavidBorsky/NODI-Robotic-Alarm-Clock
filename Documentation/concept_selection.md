# Concept selection — revision A

The objective is a recognizable alarm-clock character within a one-day digital engineering exercise. A single physical DOF would satisfy the minimum brief. Two axes are selected because directional attention and nodding communicate different intentions: yaw locates the user; pitch changes sleepy/awake posture. The display and alarm electronics are common to all concepts.

| Criterion | Weight | A: pan–tilt head | B: single-axis nodding head | C: cam-driven eyelids on fixed clock |
|---|---:|---:|---:|---:|
| Expressiveness | 40% | 5 | 3 | 3 |
| Mechanical simplicity | 10% | 3 | 5 | 3 |
| Ease of assembly | 8% | 4 | 5 | 3 |
| Manufacturing cost | 5% | 3 | 4 | 3 |
| Reliability | 7% | 3 | 4 | 3 |
| Mechanical risk | 5% | 3 | 4 | 2 |
| Electronics integration | 10% | 4 | 4 | 4 |
| Feasibility within 24 h | 15% | 4 | 5 | 3 |
| **Weighted score / 5** | **100%** | **4.13** | **3.93** | **3.05** |

Scores use 1 = poor to 5 = strong and represent engineering judgment, not measurements. Expressiveness receives the largest weight because the brief specifically asks for a character that physically wakes up with the user. Cost has a smaller weight for a one-off prototype; a production program would increase it. Feasibility includes both CAD completion and the ability to assemble from stocked servos and printed parts.

A adds one servo, a supported rotating platform and a cable service loop. Those additions explain the lower simplicity, cost, reliability and risk scores relative to B. Accessible fastening and commercial actuators keep its assembly and feasibility scores at 4. B is the preferred fallback if physical testing exposes current, cable or schedule risk. C can keep the display and electronics stationary but introduces a cam/follower, lash and small moving eyelid clearances; it provides fewer distinct gestures than head pose.

## Sensitivity and selection limits

The result is preference-sensitive. Shifting **five percentage points** from expressiveness to mechanical simplicity makes A and B tie at 4.03. Equal weights favor B: A = 3.625, B = 4.25, C = 3.0. A one-point reduction in A's expressiveness score would also reverse the decision. The matrix therefore supports the intended expressive concept; it does not establish that two axes are universally better. A physical prototype review should revisit the weighting after observing actual motion and assembly time.

The selected architecture is two direct-drive MG90S servos, a yaw platform supported by a pilot/washer interface, and a pitch head supported on the driven horn and opposite passive pivot. Restricting travel limits cable torsion and protects the desk footprint. The design avoids linkages, belts, custom gearing and closed-loop motor tuning within the challenge scope.

Scores and the sensitivity calculation are reproduced by [the engineering script](../Analysis/engineering_calculations.py); its JSON output is the numeric record.
