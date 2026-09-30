# MilkShield – SIH 2026 (PS 26110)

**Team INVICTUS · Team ID 159400**
Low-cost, lightweight milk chilling can for small-scale dairy farmers: a PUF-insulated can with reusable ice cartridges immersed in the milk – no electricity.

| Folder | Contents |
|---|---|
| `1_Presentation/` | Idea PPT (v2) – `.pptx` and `.pdf` for the portal; earlier version in `old_version_v1/` |
| `2_Video/` | Video script (PDF + Markdown) and simulation clips |
| `3_Simulation_Results/` | Charts and heat maps |
| `4_Simulation_Code/` | Python models: thermal model, parameter sweeps, wall heat-flow model, 2D CFD |

## Simulation highlights (35 °C ambient, 40 L fresh milk, 8 cartridges)
- Milk below 8 °C in ~75 min, held below 8 °C for 14 h+
- Can heat leak ≈ 22 W; lid joint identified as the main weak spot (~11 %)
- 2D CFD: natural circulation cools the whole can evenly (top to bottom within 2.5 °C)

## Re-running the models
```bash
cd 4_Simulation_Code
pip install numpy scipy matplotlib
python3 milkshield_sim.py        # thermal model
python3 sim2_sweeps.py           # cartridge / ambient / insulation sweeps
python3 sim3_wall_heatmap.py     # wall heat-flow model
python3 sim4_cfd_convection.py   # 2D CFD (~20 min), then: python3 sim4_render.py
```
