# Team guide: uploading and working together on GitHub

This repository is our shared project folder. Each person owns one main folder,
but the parts need to fit together. You do not need to learn Git commands before
uploading your first contribution.

The goal for the first milestone is a working software simulation, a preliminary
mechanical design, a wiring/power plan and an app prototype. This is evidence of
progress toward the project, not a claim that the physical device is validated.

## 1. Getting access

### Repository owner: Sreeram

1. Keep the repository private.
2. Ask each teammate for their GitHub username. A display name or email screenshot
   can be ambiguous; use the username shown in their profile URL.
3. Open the repository's **Settings** tab.
4. Under **Access**, choose **Collaborators** or **Collaborators and teams**,
   depending on what GitHub shows for the account.
5. Choose **Add people**, search the exact username and check the profile.
6. Send the repository invitation.
7. Ask the member to accept it. An invitation alone does not give access until
   they accept.
8. Share the repository URL with them. Do not make the repository public just
   because someone cannot open it.
9. Members invited to a personal private repository may have write access to the
   whole repository. Folder ownership below is a team agreement, not a security
   restriction.

The assistant has not invited anyone. The owner's steps above are instructions.

### Each teammate

1. Sign into the GitHub account that Sreeram invited.
2. Accept the invitation from your GitHub notifications or invitation email.
3. Open the repository link again.
4. Open this guide and then the README inside your own folder.
5. If you see a 404 page, first check the signed-in account and invitation.
   A private repository can appear as 404 when you do not have access.

## 2. Where to put your files

| Your job | Your folder | Typical files |
| --- | --- | --- |
| esp32 firmware & simulation | firmware/ | PillDispenser.ino, controller headers, diagram.json |
| mechanical design | mechanical/ | editable CAD, STL/STEP exports, renders |
| electronics & hardware | electronics/ | wiring diagrams, BOM, power notes |
| companion app | app/ | app source code and its setup instructions |
| communication & integration | integration/ | backend/service code and interface examples |

Shared diagrams, meeting decisions and demonstration instructions go in docs/.

A folder's README explains that part. It is not the place to paste every source
file into one long document. Keep code, CAD and diagrams as their actual files.

Use clear names such as:
- mechanical/enclosure.step
- mechanical/pill-tray.stl
- mechanical/editable/dispenser.FCStd
- electronics/wiring.pdf
- electronics/components.csv
- app/README.md
- integration/README.md

Keep the editable original as well as a convenient export. A picture of a CAD
model is useful for reviewing it, but is not a replacement for the CAD file.

## 3. Upload files using GitHub in a browser

This is the easiest route for CAD files, diagrams, PDFs, screenshots and an
initial source-code upload. You do not need a Codespace for this.

1. Open the repository and click your folder, for example **mechanical**.
2. Check the breadcrumb at the top. It should end with your folder name.
3. Choose **Add file → Upload files**.
4. Drag in the files, or use the file picker.
5. Check the listed destination paths. Avoid accidentally creating
   mechanical/mechanical/ or app/app/ by uploading the enclosing folder twice.
6. Wait for every upload to finish.
7. Write a short description, for example **add first tray model and enclosure render**.
   This description is the commit message.
8. For a first upload of entirely new files within your own folder, committing
   directly to main is fine if the team has agreed to that.
9. Choose **Commit changes**.
10. Open the uploaded files in the repository and check that they are where you
    expected. For binary CAD files GitHub may offer download instead of preview.
11. Send the team the GitHub link to your folder or contribution. Mention what
    works, what is preliminary and which question you need answered.

A **commit** is a saved version of the repository. The commit message says what
changed. GitHub keeps the earlier version, so useful filenames do not need
final-final-v7 added to them after every change.

Browser uploads allow up to 25 MiB per file and 100 files per upload. If GitHub rejects a large CAD file, keep
a smaller useful export and ask Sreeram to agree a large-file approach before
trying again. Do not upload a whole software environment or generated folders.

## 4. Edit a text file in the browser

Use this for README files, CSV tables and small changes to code.

1. Open the file, for example electronics/components.csv.
2. Click the pencil icon labelled **Edit this file**.
3. Make your change.
4. Check the preview for Markdown, or the diff if GitHub provides one.
5. Choose **Commit changes** and give a short description.
6. If the change affects another person's interface or existing code, choose
   **Create a new branch for this commit and start a pull request**.
7. Explain what changed and who should check it before merging.

Do not use the text editor for a binary CAD file, image or PDF. Upload its new
version instead.

## 5. Branches and pull requests, without the jargon

**main** holds the team's current combined work.

A **branch** is a separate working version. It lets you prepare a change without
changing main immediately.

A **pull request**, usually shortened to PR, is a page where we review the branch's
changes before combining them with main.

Use direct commits for small independent uploads in your own folder. Use a
branch and PR when changing someone else's files, changing the agreed interface,
or making a larger change that another member should review.

### Create a branch in the browser

1. Open the repository's Code tab.
2. Open the branch selector, which normally says **main**.
3. Type a descriptive name such as **mechanical/first-tray**.
4. Choose the option to create that branch from main.
5. Check that the selector now shows your new branch.
6. Upload or edit your files on that branch and commit the changes.
7. Open the **Pull requests** tab and choose **New pull request**.
8. Use **main** as the base and your branch as the compare branch.
9. Write a title such as **add preliminary tray and motor mount**.
10. In the description say what is included, what remains untested and whose
    measurements or decisions you need.
11. Ask the relevant teammate to check it. Sreeram can merge it once it fits.

If GitHub says there is a conflict, stop and tell Sreeram which file is affected.
Do not fix it by deleting the other person's work.

## 6. Write and run software locally or in Codespaces

main is the current Arduino/C++ implementation.
The original MicroPython prototype is preserved on legacy/micropython.
Most teammates can continue using browser uploads and do not need either compiler.

### Local Codex app

1. Open your existing cloned repository as the project folder.
2. Ask Codex to read docs/CODEX_HANDOFF.md.
3. Check Source Control or run git status before updating.
4. Commit your changes to a personal branch if you already have local work.
   Do not discard files to make a pull succeed.
5. Fetch updates, switch to main when the worktree is safe, and pull with --ff-only.
6. Open firmware/PillDispenser/PillDispenser.ino to work on board setup.
7. DispenserCore.h contains the shared controller; HttpSync.h and MqttSync.h contain alternate network workers.
8. Use Arduino IDE or Arduino CLI for the board build.
9. Run the checks in firmware/README.md before pushing changes.

A safe update when the working tree is clean:

~~~sh
git fetch origin
git switch main
git pull --ff-only origin main
~~~

If Git reports local changes or divergence, ask Codex to inspect the differences and preserve
both versions. Do not use reset --hard or force push to resolve routine collaboration issues.

### Codespaces

1. Open Code → Codespaces → Create codespace on main.
2. Wait for the editor and setup to complete.
3. Open Terminal → New Terminal.
4. Run python scripts/check_native.py --events for the C++ workflow checks.
5. Run python -m pytest -q for the reference API checks.
6. Run python scripts/http_demo.py for actual loopback HTTP replay.
7. Run python scripts/build_wokwi.py for the files to paste into Wokwi.
8. Follow firmware/README.md for the actual ESP32 compile.

The native check needs a C++17 compiler and downloads pinned dependencies the first time.
It does not upload to a board. Python is still used for development scripts and the reference service;
the ESP32 firmware is C++.

Save, commit and push are separate actions. A file saved only in your Codespace or on your computer
has not yet reached the team. Inspect and stage only the files you intended to change.
Stop your Codespace when finished.

### Wokwi

1. Use the Arduino ESP32 template, with sketch.ino.
2. Paste the generated output/wokwi/sketch.ino and diagram.json.
3. Install the exact libraries in output/wokwi/libraries.txt through Library Manager.
4. Run the simulation and follow firmware/README.md.
5. Copy deliberate source changes back to the repository; Wokwi does not synchronize them automatically.

Do not edit the generated sketch as the only copy of your work.
Change the canonical source under firmware/PillDispenser/ and regenerate it.

## 7. What each person should contribute

### esp32 firmware & simulation — Sreeram

Current contribution:
- Arduino/C++ FSM, scheduling, matching-user authorization and mechanism stages.
- Persistent occurrence/inventory records and event outbox.
- Versioned schedule download/acknowledgement and HTTP or simulation MQTT transport.
- Wokwi circuit, generated single-file sketch and behavioral checks.

Next work:
- Implement real motor, position, passage and fingerprint adapters after component selection.
- Measure timing and observe physical feedback.
- Coordinate shared data changes with app and integration.
- Do not use physical mode as a shortcut to enable unreviewed hardware.

### mechanical design

Submit:
- Editable compartment/tray, release path, motor mount and enclosure CAD.
- STL/STEP exports where supported.
- Outside/inside/mechanism renders and dimensions.
- A short explanation or video of how one intended dose is released.
- Answers to docs/MECHANISM_BRIEF.md.

Coordinate with electronics on actual sizes, power hardware, connectors and wire clearance.
Coordinate with firmware on homing, position numbering, release and safe stop.
The six virtual slots are provisional, not an agreed final mechanism.

### electronics & hardware

Submit:
- Exact component/model list with quantities and expected supply requirements.
- Editable circuit plus a labelled wiring/power diagram.
- A reviewed GPIO map; the existing map is only a simulation example.
- Fingerprint interface, position sensor and passage sensor specifications.
- Sensor polarity/pulse timing and motor-driver control details.

Coordinate dimensions/mounting with mechanical design and interfaces with firmware.
A generic module name is insufficient when different variants use different logic levels.
The physical passage driver must be designed from the signal; the button debounce is not its driver.

### companion app

The supplied PillPilot source and dependency files are now under app/ and connected to the shared
reference service. See app/README.md and docs/PRESENTATION.md to run it. Preserve the existing visual
design and keep setup instructions current. Do not upload node_modules, credentials or build caches.

With integration:
- Map medication records to stable schedule IDs.
- Show saved and applied-to-device as different statuses.
- Retain actual dispensed/missed/error history from the shared API.
- Preserve the UI where possible and keep its data model aligned with the device contract.
- Do not describe a dispensed event as proof the person took medication.

### communication & integration

A reference service now exists in integration/service.py.
Read integration/README.md and INTERFACE.md before replacing or extending it.

Own:
- The existing app's connection to the service or a compatible backend.
- Versioned schedule editing and device applied acknowledgements.
- Event acceptance, replay handling and duplicate suppression.
- Development deployment/device connectivity.
- Real SMS provider integration, delivery status and deduplication.

Start with the actual HTTP replay commands; then test the separate ESP32/Wokwi network path.
The generated C++ events already exercise the shared contract.
The reference service's SMS records are explicitly simulated.

## 8. Keep each folder's README useful

After uploading, answer:
1. What did you add?
2. How does someone open or run it?
3. What has been demonstrated?
4. What remains simulated, provisional or untested?
5. What exact information do you need from another teammate?

## 9. Rules that prevent avoidable problems

- Work mainly in your folder; use a branch/PR for shared changes.
- Discuss contract, dimension and pin changes before merging.
- Preserve local work before pulling; never fix a conflict by deleting someone else's contribution.
- Upload editable originals with useful exports/previews.
- Do not commit tokens, Wi-Fi passwords, patient data or biometric templates.
- Use the ignored settings.local.h for local board settings; generated Wokwi output uses safe defaults.
- Retain licences/attribution for reused source or CAD.
- Mention a blocker early with a concrete question.

## 10. Before the milestone review

Each person should demonstrate their own contribution from the shared repository.
Show software, CAD and wiring actually opening/running where possible.
State which interfaces are connected and which physical features are still pending.
Use docs/DECISIONS.md for decisions and docs/VALIDATION.md for test evidence.
