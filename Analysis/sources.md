# Analysis source register

Sources accessed 2026-10-24. Values are manufacturer information unless specifically marked as assumptions. Linked documents may change; verify the exact purchased hardware revision before manufacture.

| ID | Primary source | Information used | Limits |
|---|---|---|---|
| S1 | [Tower Pro MG90S Analog manufacturer page](https://torqpro.com/product/mg90s-analog/) | Nominal mass 13.4 g, body envelope 22.8 × 12.2 × 28.5 mm, stall torque 1.8 kgf·cm at 4.8 V, no-load transit 0.10 s/60° at 4.8 V | The page contains inconsistent higher-voltage references. All sizing uses the 4.8 V torque figure. No continuous torque or stall-current rating is supplied; the 25% operating fraction and electrical currents in this project are explicit engineering assumptions. Confirm horn, ears, shaft, cable exit and actual sample performance. |
| S2 | [Prusa Polymers PETG technical data sheet v1.1](https://prusament.com/wp-content/uploads/2022/10/PETG_Prusament_TDS_2021_10_EN.pdf) | Density 1.27 g/cm³; printed modulus 1.5 GPa in horizontal orientation; interlayer adhesion 18 ±4 MPa; HDT 68 °C | Datasheet coupon properties depend on printer, raster and process. Model uses reduced 1.0 GPa modulus and 10 MPa screening allowable; these are design assumptions, not guaranteed printed-part properties. HDT is not a safe continuous-use temperature. |

Basic mechanics equations use SI force, moment, energy and beam theory. Local gravity is approximated by standard gravity 9.80665 m/s². Fit tolerances, friction, print degradation factors, service-life targets, heat-transfer coefficients, current budgets and impact compliance are **assumptions** listed in the executable input file. They are not measurements or material certification.

No finite-element solver was successfully run for this package. The hand-calculation model is not FEA; local stress concentration, contact, creep and print anisotropy require later coupon/part tests or justified simulation.
