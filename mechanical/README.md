# 6-Compartment Automatic Pill Dispenser – 3D Printable Parts

**Compatible with** the MDP Smart Pill Dispenser project  
https://github.com/jellotheman/mdp-pill-dispenser

Designed to match the current firmware simulation assumptions:
- 6 compartments
- One preloaded item per compartment
- Servo-actuated gate for release
- Space for electronics and motor

## Files (ready to print)

| File | Description | Suggested material / settings |
|------|-------------|-------------------------------|
| `01_tray_carousel_6slot.stl` | Rotating tray with 6 radial compartments + central hub + shaft hole + indexing holes | PLA or PETG, 0.2 mm layer, 15-20% infill, no supports needed if printed flat |
| `02_base_enclosure.stl` | Main base with tray cavity, electronics bay, outlet chute, motor platform, servo pocket, feet | PLA/PETG, 0.2 mm, 20% infill |
| `03_lid.stl` | Simple lid that sits on the tray (with small central opening) | PLA, 0.2 mm, 15% infill |
| `04_servo_gate.stl` | Small flap for the outlet (hinge pin holes for 2 mm filament or M2 screw) | PETG preferred (slight flexibility), 0.15-0.2 mm |

Also included:
- `*.scad` – parametric source (edit in OpenSCAD or FreeCAD)
- `00_assembly_preview.scad` – visual check only (do not print)

## Key dimensions (mm)

- Tray outer diameter: **120**
- Tray height: **28**
- Number of compartments: **6**
- Central shaft hole: **~8.4** (for 8 mm shaft + clearance)
- Hub diameter: **22**
- Base outer diameter: **140**
- Base height: **45**
- Electronics bay (approx): **70 × 55 × 28**
- Outlet opening: **18 × 14**
- Wall thickness: **~2.2**

## Printing recommendations

1. Print the **tray** flat on the bed (floor down).
2. Print the **base** upright or on its side if your printer needs supports for the electronics bay overhang.
3. Print the **gate** flat.
4. Use **0.2 mm** layer height, **2-3 perimeters**, **15-25%** gyroid or grid infill.
5. For the shaft hole, you may need light sanding or a drill to final size depending on your printer tolerance.
6. Recommended filament: **PETG** for the tray and gate (better durability and less warping with temperature changes). PLA is fine for prototypes.

## Assembly outline

1. Mount a small servo (SG90 / MG90S) or stepper in the base so its shaft comes up through the central platform.
2. Attach a coupler / hub to the motor shaft and fix the tray on top (set screw or friction fit).
3. Align one compartment with the outlet chute.
4. Install the servo gate over the outlet so the servo horn can open/close it.
5. Place the lid on top.
6. Route wires from the electronics bay to the ESP32 / motor driver.

The current firmware still runs in **simulation profile**. You will need to implement the real `Mechanism` driver (homing, select, release, passage sensor) once the physical hardware is chosen – see `docs/MECHANISM_BRIEF.md` in the repository.

## How to modify

Open any `.scad` file in **OpenSCAD** (free) or import into **FreeCAD**.  
All important sizes are variables at the top of `generate_dispenser.py`.  
Re-run the Python script or edit the SCAD directly, then export new STLs.

## Licence / attribution

Student project parts. Feel free to modify.  
If you reuse significant geometry from other open-source dispensers, check their licences and credit them in the repository as required by the team guide.
