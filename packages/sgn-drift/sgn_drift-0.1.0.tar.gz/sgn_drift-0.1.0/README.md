# SGN-Drift

**Geometric Spectral Diagnostics for Gravitational Wave Detectors.**

`sgn-drift` is an extension to the [SGN](https://git.ligo.org/greg/sgn) framework designed to quantify the stability of
the detector noise floor using Information Geometry.

## Installation

```bash
pip install sgn-drift
```

## Example Usage

### Command Line

```bash
sgn-drift-estimate --detector L1 --start 1263085000 --end 1263089096 --output drift_L1.csv --bands "low:10:50,mid:50:300"
```

### Python API

```python
from sgndrift.bin.estimate_drift import estimate_drift

bands = {
    "v_low": (10, 50),
    "v_mid": (50, 300)
}

estimate_drift(
    start=1262600000,
    end=1262604096,
    detector="L1",
    output_drift="analysis.csv",
    bands=bands,
    verbose=True
)
```
