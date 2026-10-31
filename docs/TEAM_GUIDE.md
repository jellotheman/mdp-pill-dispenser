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
| esp32 firmware & simulation | firmware/ | main.py, pysm.py, diagram.json |
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

## 6. Write and run software in Codespaces

A Codespace is a development computer opened in your browser. It lets you run
Python and use a terminal without installing tools on your own computer.

1. Open the repository.
2. Choose **Code → Codespaces → Create codespace on main**.
3. Wait for the editor and automatic setup to finish.
4. The Explorer on the left shows the project folders.
5. Open **Terminal → New Terminal** if the terminal is hidden.
6. Run firmware tests with **python -m pytest -q**.
7. Run the automatic firmware demo with **python scripts/demo.py**.
8. Use **python scripts/demo.py --interactive** for a manual terminal demo.
9. Make changes in your own folder.
10. Before finishing, use Source Control to inspect the changed files, stage only
    your contribution, enter a commit message and commit.
11. Use **Sync Changes** or **Push** to send the commit to GitHub.

Saving a file in the editor and pushing a commit are different actions. A file
saved only in your Codespace is not yet available to the rest of the team on main.

Stop the Codespace from the Codespaces menu when finished. Closing a browser tab
does not necessarily stop it immediately. Codespaces uses the allowance and
billing settings of the account creating it. Each member can choose browser
uploads instead when they only need to submit files.

Our configuration sets up firmware Python tools only. The app member may need
additional tools once their framework is chosen; agree them before changing
shared configuration.

## 7. What each person should contribute

### esp32 firmware & simulation — Sreeram

Submit:
- MicroPython code for the schedule, authorization and dispensing state machine.
- A Wokwi circuit and instructions showing the complete simulated cycle.
- Examples of invalid authentication, missed dose and failed dispensing.
- JSON output that the integration member can parse.
- Tests and a short note distinguishing simulation from completed hardware.

Coordinate with electronics on pins, modules and electrical interfaces.
Coordinate with mechanical design on what one motor command physically means.
Coordinate with integration on schedule fields and event meanings.

### mechanical design

Submit:
- A preliminary editable 3D model of the tray/compartments, dispensing path,
  motor mount and outer enclosure.
- STL files for printed parts and STEP exports where the tool supports them.
- Two or three renders/screenshots showing the outside and internal arrangement.
- Key dimensions, motor assumptions and assembly notes.
- A short description or animation explaining how a dose leaves the compartment.

Coordinate with electronics before placing boards, connectors or power hardware.
Ask for actual component dimensions and leave space for wires and service access.
Coordinate with Sreeram before choosing a stepper carousel, servo gate or a
different mechanism. The current firmware servo is a demonstration adapter.

Do not label a CAD-only mechanism as physically tested. Identify dimensions that
still depend on component selection.

### electronics & hardware

Submit:
- A component list with part/model names, quantities and approximate costs.
- A circuit/wiring diagram with power and ground connections.
- A reviewed GPIO table, replacing the provisional map after agreement.
- A power plan: supply voltage/current, motor supply, common ground and any driver
  or level conversion needed.
- The expected fingerprint interface and motor control interface.

Coordinate with mechanical design on dimensions, mounting and connector access.
Coordinate with Sreeram before changing pins or module types.
Coordinate with integration on whether notifications will use Wi-Fi or a GSM
module. Do not purchase a module solely because a reference project used it.

The Wokwi circuit is a simulation aid, not an approved physical wiring plan.

### companion app

Submit:
- Source code for a small working interface, not screenshots alone.
- A screen to add/edit/enable medication schedules.
- A dispensing-history screen with due, dispensed, missed and error states.
- A README describing the framework and exact start command.
- A clear label when the app is showing mock data.

Coordinate with integration on the API and the fields in integration/INTERFACE.md.
Use mock responses while the backend is being built. Do not independently invent
a second incompatible schedule format.

Do not label a dose as taken when the only evidence is that the dispenser
released it. The first version does not need accounts or a cloud service.

### communication & integration

Submit:
- A small backend/service or agreed device transport, with a start command.
- A way to receive schedules from the app and expose dispensing history.
- A replay script that feeds the firmware's sample JSON events into your service.
- Mock SMS behaviour that clearly says no real SMS was sent.
- An example showing one schedule and one resulting history entry.

Coordinate with the app member on request/response shapes and with Sreeram on
firmware events. Start with replayed JSON so no one is blocked by Wokwi networking.

The initial firmware emits events over the serial console. It does not include
a live HTTP/MQTT connection. Choose the transport together and update the
interface document before building that connection.

A queued SMS request is not proof of SMS delivery. Handle delivery separately
when real messaging is added.

## 8. Keep each folder's README useful

After a contribution, answer:
1. What files did you add?
2. How does someone open or run them?
3. What works already?
4. What is still a draft or simulation?
5. What do you need from another member?

Five clear answers are more useful than several pages of copied background.

## 9. Rules that prevent avoidable problems

- Work mainly in your own folder.
- Discuss interface, dimension and pin changes before committing them.
- Check the latest main before editing a shared file.
- Use a branch/PR for changes that affect someone else's work.
- Include editable originals and any useful previews.
- Do not upload passwords, API keys, Wi-Fi credentials or real patient data.
- Do not upload node_modules, virtual environments, temporary build outputs,
  copied download caches or unrelated personal files.
- Keep licences/attribution for reused code or CAD.
- Use a short commit message that explains the change.
- Mention blockers early, with a concrete question.

## 10. Before the milestone review

Each person should be able to open their folder and demonstrate their contribution.
Show the simulation, CAD, wiring plan, app or service actually working where
possible. Say what is connected today and what is still mocked. Keep one short
list of decisions the team must make next in docs/DECISIONS.md.
