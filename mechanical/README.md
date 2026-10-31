# Mechanical design

Start with [the team guide](../docs/TEAM_GUIDE.md), particularly the browser-upload
steps and your role's deliverables.

## Put these here
- editable/: source CAD from FreeCAD, Fusion, SolidWorks, OpenSCAD or your chosen tool.
- exports/: STL files for printable parts and STEP exports for exchanging geometry.
- renders/: clear outside, inside and mechanism views.
- assembly.md: dimensions, assembly order, motor assumption and outstanding questions.

Upload actual design files, not only screenshots. You may create these subfolders
when you have files for them; GitHub does not store empty folders.

## First milestone
Show the compartments, dispensing path, motor mount, enclosure and reserved
electronics space. Include enough dimensions for the electronics person to check
fit. Explain how one actuator command releases the intended dose.

The current firmware shows a single servo gate for simulation. It does not commit
the team to that mechanism or implement a stepper carousel. Agree the real
mechanism with firmware and electronics before refining the motor mount.

## References
- https://github.com/Willykengineering/Automatic-Supplement-Pill-Dispenser
- https://github.com/Shaztech/Pilldispenser
- https://github.com/Elegiac-Quantum/mendo-pill-dispenser

Inspect licensing before reusing models; public access alone is not permission
to redistribute or modify them. List any reused files and their source/licence.

## Add a progress note after uploading
What opens with which tool? What is modelled? What is physically tested? Which
dimensions are provisional? What do you need from electronics or firmware?
