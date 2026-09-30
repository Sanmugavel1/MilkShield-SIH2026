# MilkShield – SIH 2026 video script (≈ 2 min)

About 295 spoken words (≈ 2 min). Speak at a calm pace (~150 words/min); pause briefly at each "▸".
All clips and images are in `~/milkshield-sim/`; the deck is `~/Downloads/MilkShield_SIH2026_Idea_PPT_v2.pptx`.

| Time | On screen | Narration |
|---|---|---|
| **0:00 – 0:12** | Slide 1 (title) | "Hello, we are Team INVICTUS, solving problem statement 26110: a low-cost, lightweight milk chilling can. ▸ Milk leaves the cow at about 35 °C and travels for hours in plain metal cans." |
| **0:12 – 0:30** | Slide 2 (proposed solution) | "Our solution is **MilkShield**: a double-walled, foam-insulated can with a food-grade liner. ▸ Reusable ice cartridges hang from the lid, **right inside the milk** – the cold goes straight in, and the foam keeps the heat out. No compressor, no electricity." |
| **0:30 – 0:45** | Slide 3 (technical approach) – point along the top flow | "Fill, drop in frozen cartridges, seal, and go. ▸ At the collection centre, cartridges are swapped for frozen ones. ▸ The cartridge count is our design knob: two for pre-chilled milk, six for 30 litres, eight for 40." |
| **0:45 – 1:00** | `sim1_lumped_animation.mp4` | "We sized it through simulation at three levels. ▸ First, a thermal model: on a 35 °C day, a plain can stays at 35. ▸ MilkShield brings 40 litres below 8 °C in 75 minutes and holds it there for over 14 hours." |
| **1:00 – 1:12** | `sim3_wall_heatmap.png` (zoom to right half) | "Second, a heat-flow model of the walls. ▸ The foam carries the full temperature drop, and the model found the one weak spot – the lid joint – which our design insulates." |
| **1:12 – 1:30** | `sim4_cfd_convection.mp4` (12 s), then `sim4_cfd_snapshots.png` | "Third, CFD of the milk itself. ▸ Cold milk slides down the ice, sweeps the bottom and rises through the centre – **the can stirs itself**. ▸ Top and bottom stay within about two and a half degrees, and the CFD cools even faster than our thermal model, so our numbers are on the safe side." |
| **1:30 – 1:42** | Slide 4 (feasibility) | "It's practical: food-grade materials, a prototype for 6 to 13 thousand rupees, and rotomoulding for scale." |
| **1:42 – 1:55** | Slide 5 (impact), then Slide 6 (comparison table) | "It serves small farmers, collection centres and remote hilly and North-East villages – safe milk with no power bill and no diesel. ▸ And it's the only modular design among existing options." |
| **1:55 – 2:05** | Slide 6 – hold on the green "Simulation study" box | "Next, we build the prototype for field trials at a village collection centre. ▸ Thank you." |

---

## How to explain each simulation (if you want to say more, or a judge asks)

**1. Thermal model – "how cold, how fast, how long"**
Treats the milk and the ice cartridges as two linked thermal masses. Heat leaks in through the walls, and the ice absorbs heat while it melts at 0 °C. It gives the temperature curve and the cartridge count for each load.
*One line:* "It's the energy budget of the can, solved minute by minute over 24 hours."

**2. Wall heat-flow model – "where the heat gets in"**
A finite-volume heat-conduction model of the can's cross-section at 1 mm resolution: shell, foam, liner, lid and lid joint. It found a total leak of about 22 W at 35 °C: roughly 70 % through the side wall, 18 % through the lid, 12 % through the bottom. The solid-plastic lid joint alone accounts for about 11 %.
*One line:* "It shows exactly where heat sneaks in, so we can fix that spot in the design."

**3. CFD – "does all the milk get cold, or just the milk near the ice?"**
A 2D natural-convection simulation of a vertical slice through the can. Cold milk is heavier, so it sinks along the cartridges and sets up a circulation loop. The whole can cools together, and the last spot to cool is the centre-bottom, below the cartridges. That tells us to keep cartridges long, reaching close to the floor.
*One line:* "The ice makes the milk stir itself, so the whole can cools evenly."

## Likely judge questions

| Question | Answer |
|---|---|
| "Which software did you use?" | "Our own Python models: a lumped thermal model, a finite-volume heat-conduction model of the walls, and a 2D CFD solver. Each assumption is listed at the top of its file, so every number can be traced." |
| "How reliable are the results?" | "Three separate models point the same way: the CFD cools even faster than the thermal model, and the wall model's heat leak is lower than the value we designed for. So our slide figures are on the cautious side. The prototype trials will fine-tune them." |
| "Won't the milk go below 4 °C?" | "It settles around 2 °C, because ice sits at 0 °C. That's safe: Codex sets only an upper limit, and milk freezes at about −0.5 °C, so it cannot freeze." |
| "Why not ANSYS?" | "At idea stage, a transparent model we can explain line by line is more useful. With the prototype we'll move to a full 3D run to refine the lid and cartridge layout." |
| "What if it's a 45 °C day?" | "Our simulation still holds the milk below 8 °C for over 10 hours with the same 8 cartridges." |
| "How heavy is it?" | "A full 40-litre trip needs 8 cartridges – 16 kg of ice. Lighter loads carry fewer." |

## Recording tips
- Record the slides in PowerPoint's slideshow mode; drop the MP4 clips (1280×720) in between in your video editor.
- Keep each still on screen for at least 5 s, and use a slow zoom on the heat map and CFD snapshots.
- Add a small corner caption "Simulation" on the three simulation shots – it looks professional and matches the deck.
- Rehearse once with a timer. If you run long, shorten the 1:42 impact line first.
