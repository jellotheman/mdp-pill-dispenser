# Companion app

This folder is reserved for the app member's contribution; no app has been
implemented by the firmware work.

Read [the team guide](../docs/TEAM_GUIDE.md) for uploading and collaboration steps,
and [the shared interface](../integration/INTERFACE.md) before choosing data fields.

## First milestone
Build a small working web/mobile interface with:
- add/edit/enable medication schedules;
- dispensing history using due, dispensed, missed and error states;
- clearly labelled mock data while integration is in progress.

Use an established framework you can run and explain. Agree the choice with the
integration member. Avoid adding accounts, cloud services or unnecessary screens
for this milestone.

## Upload
Include actual source files, framework dependency files and a README with:
1. framework and required runtime;
2. exact installation/start commands;
3. implemented screens;
4. what is mock and what reaches the backend;
5. outstanding API questions.

Do not upload node_modules, build caches, credentials or virtual environments.
Use a branch/PR if your setup needs to change shared root configuration.

Do not label a dispensed event as medication taken. The prototype has no evidence
of ingestion. Changing a schedule in an app mock is not evidence the ESP32
received it; show synchronization separately when the transport is connected.
