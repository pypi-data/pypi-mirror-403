# spacekernel

SpaceKernel (Space Mission Engineering Tools) is a Python package providing a robust and extensible ecosystem for Earth satellite services, mission analysis, and space situational awareness (SSA).
It offers fast orbit propagation, maneuver simulation, coverage analysis, and powerful 2D/3D visualization, all designed for research and operational workflows.

## Features

- *Accurate Orbit Propagation:* Support for multiple integration methods and perturbation models, including J2, atmospheric drag, lunisolar, and SRP effects.

- *Maneuver Modeling:* Apply and analyze maneuvers with custom parameters and easy scenario setup.

- *Payload Coverage & Access:* Tools for computing payload coverage, contact windows, and access analysis.

- *Visualization:* High-quality 2D and 3D visualization for orbits, ground tracks, stations, and coverage footprints.

- *High Performance:* Cython-powered for speed.


## Third-Party Licenses

### IAU SOFA

This project includes unmodified third-party software from the IAU SOFA collection:

    IAU SOFA Software Library (C Edition)
    Copyright (c) 2009–2023 International Astronomical Union

This software is distributed under the terms of the SOFA license, included in
LICENSE-SOFA.txt. For more information, visit https://www.iausofa.org.

### SGP4

This project includes unmodified third-party software from the CelesTrak 
Fundamentals of Astrodynamics repository:

    SGP4.cpp and SGP4.h
    Copyright (c) Free Software Foundation

These files are distributed under the terms of the GNU Affero General Public 
License v3.0. The full license text is available in `LICENSE-SGP4.txt`. For 
more information, visit https://github.com/CelesTrak/fundamentals-of-astrodynamics.