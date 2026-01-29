#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

cdef extern from "SGP4DC.h" namespace "SGP4DC":
    # Observation record structure
    ctypedef struct obsrec:
        int sennum
        long satnum
        int year, mon, day, hr, min
        double jd, jdf, sec, dtmin, lst
        int error
        char init, method
        double rsecef[3]
        double vsecef[3]
        int obstype
        double x, y, z, xdot, ydot, zdot, bstar
        double rng, az, el, drng, daz, del_
        double rtasc, decl, trtasc, tdecl

    # Sensor record structure
    ctypedef struct senrec:
        int sennum
        char senname[10]
        double senlat, senlon, senalt
        double rngmin, rngmax, azmin, azmax, elmin, elmax
        double biasrng, biasaz, biasel, biasdrng, biasdaz, biasdel
        double biastrtasc, biastdecl
        double noisex, noisey, noisez, noisexdot, noiseydot, noisezdot, noisebstar
        double noiserng, noiseaz, noiseel, noisedrng, noisedaz, noisedel
        double noisetrtasc, noisetdecl