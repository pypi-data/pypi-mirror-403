# SGN-Drift Documentation

**SGN-Drift** provides a specialized toolkit for analyzing the non-stationarity of gravitational wave detector noise. It
builds upon the `sgn-ligo` ecosystem to provide real-time and offline estimates of spectral stability.

## Key Features

* **Fisher Velocity Metric:** Implements the rigorous geometric definition of spectral drift (Paper A2).
* **Band-Limited Analysis:** Decompose instability into frequency bands (e.g., distinguishing Scattering from Whistles).
* **Recursive Estimators:** Includes fast, infinite-impulse-response (IIR) PSD estimators for low-latency tracking.
* **SGN Integration:** Fully compatible with GStreamer-based pipelines via the `sgn` framework.

## Component Overview

| Component        | Description                                                             |
|:-----------------|:------------------------------------------------------------------------|
| `FisherVelocity` | Transform element that calculates the drift metric between PSD frames.  |
| `RecursivePSD`   | Fast PSD estimator suitable for tracking rapidly changing noise floors. |
| `DriftCSVSink`   | Specialized sink for writing sparse drift event data to disk.           |

## Getting Started

Check the [API Reference](api/util/psd_estimators.md) for details on the underlying mathematics, or see the `bin/`
directory for example scripts.
