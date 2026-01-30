"""
The processors module.

Provides Processor objects to analyze data in the context of pulsed magnetic field
experiments. The Processor objects should be initialized with a configuration file.

BaseProcessor
-------------
The `BaseProcessor` class contains the basic object logic and data storage (as Data
objects from the `pyuson.data` module). It has some generic methods to load binary data,
integrate a pickup voltage to get the magnetic field over time, as well as saving data
and metadata as a NeXus HDF5 file.

It provides an interface to set and get data in a format expected by the NeXus standard.
It has two main attributes, `data_raw` (NXdata) and `data_processed` (NXprocess).

The former holds the raw data as measured during the experiment while the latter
contains data that have undergone any analysis, even trivial.

`data_processed` hosts any numbers of NXdata subgroups, where the first are general
results of the experiment (such as the magnetic field), and the following ones are data
specific to a so-called 'serie', for example different time windows or different
analysis parameters. The current serie index is monitored with the `idx_serie` property.

The `set_data_serie()` and `get_data_serie()` methods act has setter and getter methods
for the currently selected serie index in order to target the data at the correct
location (i.e. `data_processed["results_serie{idx_serie}"]`).

This class should mainly be used for subclassing to build more specialized Processors.

EchoProcessor
-------------
The `EchoProcessor` is a Processor class specific for ultra-sound experiments. Here,
series are echoes (thus, the `idx_serie` property tracks the echo index), and the aim is
to derive the attenuation and phase-shift of an ultra-sound wave going through a sample
during a high-intensity pulsed magnetic field shot.

It provides loader methods for both LabVIEW binary files as well as Tektronix WFM files.
It can perform demodulation of a signal given a reference (digital mode), or work
directly with the three channels (amplitude, in-phase and out-of-phase -- analog mode).

It is assumed that the data is measured in the form of so-called 'frames' that are
acquired during a shot (pulsed magnetic field, time scale : 0.5s), where one frame is
a time serie of samples acquired at high-speed (time scale : 5µs). The whole-experiment
time scale is referred to as "experiment" while the single-frame time-scale is referred
to as "measurement".

Methods allow to shape the data in order to end up with one 2D array per measurements,
compute the average in a given measurement time window and derive the attenuation and
phase-shift.

Optionally, the raw data can be smoothed and downsampled before averaging. Demodulation
can be tuned either by changing the radio-frequency (center frequency, f0) and filter
cut-off frequency, and decimation is possible to smooth the signal.
"""

from ._base import BaseProcessor
from ._echo import EchoProcessor

__all__ = ["BaseProcessor", "EchoProcessor"]
