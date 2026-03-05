### Nonlinear six degrees of freedom dynamic simulation of USV for MATC team competing in PEP 26
---
Initial development done with VPython in Axes Dev \
Main 6-DoF model in Model, details can be found [here](https://docs.google.com/document/d/1pb3P5QaangbH325uTRs-FefswTTehO3T3uK7tuayAIE/edit?pli=1&tab=t.psa2r2w88iyw)
- Simulation & model implementation done in Python with NumPy and SciPy
- Visualization done in JavaScript with Three.js

To start simulation, run server.bat in Model folder. Ensure Python is installed and dependencies listed in requirements.txt are installed. \
To start visualization, run server.bat in Model/visualization. Ensure NodeJS is installed and dependencies listed in package.json are installed.

Telemetry for visualization is broadcasted on localhost:9000, visualization server is started on localhost:9900.
