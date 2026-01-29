#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from setuptools import Extension, setup, find_packages  # must be on top

import sys
import numpy
from Cython.Build import cythonize
from pathlib import Path

# ========== ========== ========== ========== ========== ========== ext_modules
cython_compiler_directives = {
    'language_level': '3',
    'embedsignature': True,
    'cdivision': True,
    'boundscheck': False,  # Cython is free to assume that indexing operations ([]-operator) in the code will not cause any IndexErrors to be raised
    'wraparound': False,  # Cython is allowed to neither check for nor correctly handle negative indices, possibly causing segfaults or data corruption.
    'profile': False,
    # 'linetrace': True,
    # 'binding': True
}
"""Refer to
https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html#compiler-directives
"""

# ========== ========== ========== ========== ========== ========== sgp4
sgp4_src_file = [Path('spacekernel/propagators/analytical/sgp4/SGP4.cpp').__str__(),]

# ========== ========== ========== ========== ========== ========== sgp4dc
# sgp4dc_src_file = [
#     Path('spacekernel/od/sgp4dc/SGP4.cpp').__str__(),
#     Path('spacekernel/od/sgp4dc/AstroLib.cpp').__str__(),
#     Path('spacekernel/od/sgp4dc/MathTimeLib.cpp').__str__(),
# ]

# ========== ========== ========== ========== ========== ========== sofa
sofa_src_dirpath = Path('spacekernel/sofa/src')
sofa_src_files = [str(file) for file in sofa_src_dirpath.iterdir()
                  if file.suffix == '.c' and file.stem != 't_sofa_c']

# ========== ========== ========== ========== ========== ========== macros
platform_specific_macros = []

if sys.platform == "linux":
    openmp_compile_args = ['-fopenmp']
    openmp_link_args = ['-fopenmp']

elif sys.platform == "darwin":
    # macOS with Apple Clang requires -Xpreprocessor flag
    openmp_compile_args = ['-Xpreprocessor', '-fopenmp']
    openmp_link_args = ['-lomp']

elif sys.platform.startswith("win"):
    openmp_compile_args = ['/openmp']
    openmp_link_args = ['/openmp']
    sgp4_src_file.append(Path('spacekernel/propagators/analytical/sgp4/sgp4imp.cpp').__str__())

else:
    raise ValueError("Unsupported platform")

# ========== ========== ========== ========== ========== ========== extensions
options = {
    'include_dirs': [numpy.get_include()],
    'define_macros': [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")] + platform_specific_macros,
}

extensions = [

    Extension(
        name='spacekernel.utils.representable',
        sources=['spacekernel/utils/representable.pyx'],
        **options),

    Extension(
        name='spacekernel.units.units',
        sources=['spacekernel/units/units.pyx'],
        **options),

    Extension(
        name='spacekernel.datamodel.structured',
        sources=['spacekernel/datamodel/structured.pyx'],
        **options),

    # ========== ========== ========== ========== ========== mathtools
    Extension(
        name='spacekernel.mathtools.misc.misc',
        sources=['spacekernel/mathtools/misc/misc.pyx'],
        **options),

    Extension(
        name='spacekernel.mathtools.vectools.vectools',
        sources=['spacekernel/mathtools/vectools/vectools.pyx'],
        **options),

    Extension(
        name='spacekernel.mathtools.matrix.matrix',
        sources=['spacekernel/mathtools/matrix/matrix.pyx'],
        **options),

    # ========== ========== ========== ========== ========== ellipsoid
    Extension(
        name='spacekernel.mathtools.ellipsoid.ellipsoid',
        sources=['spacekernel/mathtools/ellipsoid/ellipsoid.pyx'] + sofa_src_files,
        **options),

    # ========== ========== ========== ========== ========== iers
    Extension(
        name='spacekernel.iers.bulletins',
        sources=['spacekernel/iers/bulletins.pyx'] + sofa_src_files,
        **options),

    Extension(
        name='spacekernel.iers.eop',
        sources=['spacekernel/iers/eop.pyx'] + sofa_src_files,
        **options),

    # ========== ========== ========== ========== ========== time
    Extension(
        name='spacekernel.time.format',
        sources=['spacekernel/time/format.pyx'] + sofa_src_files,
        **options),

    Extension(
        name='spacekernel.time.scale',
        sources=['spacekernel/time/scale.pyx'] + sofa_src_files,
        **options),

    Extension(
        name='spacekernel.time.time',
        sources=['spacekernel/time/time.pyx'] + sofa_src_files,
        **options),

    # ---------- ---------- ---------- ---------- STM
    Extension(
        name='spacekernel.mathtools.stm.stm',
        sources=['spacekernel/mathtools/stm/stm.pyx'],
        **options),

    # ========== ========== ========== ========== ========== frames
    Extension(
        name='spacekernel.frames.rotations',
        sources=['spacekernel/frames/rotations.pyx'] + sofa_src_files,
        extra_compile_args=openmp_compile_args,
        extra_link_args=openmp_link_args,
        **options),

    Extension(
        name='spacekernel.frames.geocentric',
        sources=['spacekernel/frames/geocentric.pyx'] + sofa_src_files,
        extra_compile_args=openmp_compile_args,
        extra_link_args=openmp_link_args,
        **options),

    Extension(
        name='spacekernel.frames.frames',
        sources=['spacekernel/frames/frames.pyx'] + sofa_src_files,
        **options),

    # ========== ========== ========== ========== ========== state
    Extension(
        name='spacekernel.state.coe',
        sources=['spacekernel/state/coe.pyx'],
        **options),

    Extension(
        name='spacekernel.state.state',
        sources=['spacekernel/state/state.pyx'],
        **options),

    Extension(
        name='spacekernel.state.ephemeris',
        sources=['spacekernel/state/ephemeris.pyx'],
        **options),

    # ========== ========== ========== ========== ========== bodies
    Extension(
        name='spacekernel.bodies.bodies',
        sources=['spacekernel/bodies/bodies.pyx'] + sofa_src_files,
        **options),

    # ========== ========== ========== ========== ========== propagator
    Extension(
        name='spacekernel.propagators.propagators',
        sources=['spacekernel/propagators/propagators.pyx'],
        **options),

    Extension(
        name='spacekernel.propagators.analytical.keplerian.keplerian',
        sources=['spacekernel/propagators/analytical/keplerian/keplerian.pyx'],
        **options),

    Extension(
        name='spacekernel.propagators.analytical.sgp4.tle',
        sources=['spacekernel/propagators/analytical/sgp4/tle.pyx'],
        **options),

    Extension(
        name='spacekernel.propagators.analytical.sgp4.sgp4imp',
        sources=['spacekernel/propagators/analytical/sgp4/sgp4imp.pyx'] + sgp4_src_file,
        language='c++',
        **options),

    # ========== ========== ========== ========== ========== od
    # Extension(
    #     name='spacekernel.od.sgp4dc.wrap',
    #     sources=['spacekernel/od/sgp4dc/wrap.pyx'] + sgp4_src_file,
    #     language='c++',
    #     **options),

    # ========== ========== ========== ========== ========== ssa
    Extension(
        name='spacekernel.ssa.maneuver_solver.solver',
        sources=['spacekernel/ssa/maneuver_solver/solver.pyx'],
        **options),

    # ========== ========== ========== ========== ========== satellite
    Extension(
        name='spacekernel.satellite.satellite',
        sources=['spacekernel/satellite/satellite.pyx'],
        **options),

    # ========== ========== ========== ========== ========== satellite
    Extension(
        name='spacekernel.scenario.scenario',
        sources=['spacekernel/scenario/scenario.pyx'],
        **options),

]

here = str(Path(__file__).parent.absolute())

ext_modules = cythonize(extensions,
                        annotate=True,
                        compiler_directives=cython_compiler_directives,
                        include_path=[here, numpy.get_include()],
                        language_level=3)


# ========== ========== ========== ========== ========== ========== setup
setup(
    # packages=find_packages(
    #     include=["spacekernel", "spacekernel.*"],
    #     exclude=['test', 'test.*', 'mdtk', 'mdtk.*']),
    # packages=[
    #     'spacekernel',
    #     'spacekernel.bodies',
    #     'spacekernel.ccsds',
    #     'spacekernel.datamodel',
    #     'spacekernel.frames',
    #     'spacekernel.iers',
    #     'spacekernel.mathtools',
    #     'spacekernel.mathtools.ellipsoid',
    #     'spacekernel.mathtools.integrators',
    #     'spacekernel.mathtools.matrix',
    #     'spacekernel.mathtools.misc',
    #     'spacekernel.mathtools.stm',
    #     'spacekernel.mathtools.vectools',
    #     'spacekernel.propagators',
    #     'spacekernel.propagators.analytical',
    #     'spacekernel.propagators.analytical.keplerian',
    #     'spacekernel.propagators.analytical.sgp4',
    #     'spacekernel.propagators.numerical',
    #     'spacekernel.satellite',
    #     'spacekernel.sofa',
    #     'spacekernel.state',
    #     'spacekernel.time',
    #     'spacekernel.units',
    #     'spacekernel.utils'
    # ],
    ext_modules=ext_modules,
    include_package_data=True,
    zip_safe=False)