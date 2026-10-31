# Demonstration checklist

## Native workflow and real HTTP replay

From the repository root:

~~~sh
python -m pip install -r requirements-dev.txt
python scripts/check_native.py --events
python -m pytest -q
python scripts/http_demo.py
python scripts/build_wokwi.py
~~~

The native runner checks the actual shared C++ controller and pinned community libraries.
The HTTP replay starts a temporary API and proves message acceptance/idempotency.
Neither command emulates the ESP32 processor or physical mechanism.

## Wokwi

Follow firmware/README.md to paste the generated sketch and circuit into an Arduino ESP32 project.
Install the libraries listed in libraries.txt; no custom library upload is required.

Demonstrate:
1. Incorrect matching leaves the mechanism unauthorized.
2. Correct matching causes virtual homing/indexing, then visible servo release.
3. One blue passage during release/verification produces dispensed.
4. No matching produces missed.
5. Authorization without a passage produces ERROR and no retry.
6. A blue input held before release prevents opening.
7. Used compartments remain spent after the occurrence completes.

The default timer demonstration has events at 5, 35 and 65 seconds.
Use erase-demo only for disposable simulation data when repeating the demonstration.

## Optional connected demonstration

Start the reference service and configure a reachable backend in the sketch.
Disable DEMO_TIMERS and enable networking.
Save a future daily schedule through the service, observe applied_revision,
then complete a Wokwi cycle and fetch its history.

This connected ESP32 path must be run and observed separately; compilation and HTTP replay do not prove it.
The existing app is still awaiting source upload, so there is no claim that its UI is integrated.

## Explain accurately

Homing/indexing and both sensors remain simulations.
The reference service creates mock SMS records, not real SMS delivery.
A passage does not prove medication ingestion.
The physical profile remains blocked pending construction-specific drivers.
