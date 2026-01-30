# Cₛ Core (ONI Framework)

**Mathematical API for detection signatures and anomaly validation in brain-computer interfaces.**

[![PyPI version](https://badge.fury.io/py/oni-framework.svg)](https://badge.fury.io/py/oni-framework)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/qikevinl/ONI/actions/workflows/tests.yml/badge.svg)](https://github.com/qikevinl/ONI/actions/workflows/tests.yml)

---

## Core Equations

### Coherence Score (Cₛ)

The foundation of anomaly detection — a trust score from 0 to 1:

```
Cₛ = e^(−(σ²φ + σ²τ + σ²γ))
```

| Symbol | Name | What It Detects |
|--------|------|-----------------|
| **σ²φ** | Phase variance | Timing jitter, desynchronization attacks |
| **σ²τ** | Transport variance | Pathway degradation, signal injection |
| **σ²γ** | Gain variance | Amplitude manipulation, surge attacks |

**Output:** 1.0 = perfect trust, 0.0 = anomaly detected

### Scale-Frequency Invariant

Validates biological plausibility of neural signals:

```
f × S ≈ k (constant)
```

| Variable | Meaning |
|----------|---------|
| **f** | Signal frequency (Hz) |
| **S** | Spatial scale (meters) |
| **k** | Biological constant (~0.004) |

**Use case:** Detect impossible signals (e.g., 500 Hz oscillation at whole-brain scale).

---

## What This API Does

Build detection signatures for neural signal anomalies:

```python
from oni import CoherenceMetric, NeuralFirewall, ScaleFrequencyInvariant

# 1. Calculate trust score from signal data
metric = CoherenceMetric(reference_freq=40.0)
cs = metric.calculate(arrival_times, amplitudes)  # → 0.0 to 1.0

# 2. Make accept/reject decisions
firewall = NeuralFirewall(threshold_low=0.3, threshold_high=0.6)
result = firewall.filter(signal)  # → ACCEPT, REJECT, or FLAG

# 3. Validate biological plausibility
sfi = ScaleFrequencyInvariant()
valid = sfi.validate(frequency=40, spatial_scale=1e-4)  # → True/False
```

**This is an API, not a measurement tool.** It provides mathematical primitives — you supply the signal data from your BCI hardware.

---

## Quick Reference

| Function | Input | Output | Use For |
|----------|-------|--------|---------|
| `CoherenceMetric.calculate()` | timestamps, amplitudes | 0.0–1.0 | Anomaly scoring |
| `NeuralFirewall.filter()` | Signal object | ACCEPT/REJECT/FLAG | Access control |
| `ScaleFrequencyInvariant.validate()` | frequency, scale | True/False | Plausibility check |
| `ONIStack.layer(n)` | layer number | Layer object | Architecture reference |

---

## Package Architecture

> **This package is the core API library.** For educational content and interactive learning, see [ONI Academy](../oni-academy/ONI_ACADEMY.md) (`pip install oni-academy`).

```
oni-framework (pip install oni-framework)
│
└── Core Library (oni/)
    ├── coherence.py      # Cₛ signal trust scoring
    ├── firewall.py       # Zero-trust signal filtering
    ├── layers.py         # 14-layer ONI model
    ├── scale_freq.py     # f × S ≈ k invariant
    └── neurosecurity/    # Kohno threat model, BCI Anonymizer
```

| Package | Purpose | Install |
|---------|---------|---------|
| **oni-framework** | Core API for BCI security (this package) | `pip install oni-framework` |
| **oni-academy** | Educational platform, tutorials, interactive learning | `pip install oni-academy` |
| **oni-tara** | Security monitoring & attack simulation platform | `pip install oni-tara` |

**Use oni-framework when you need:**
- Security primitives for your BCI application
- Coherence scoring in your signal processing pipeline
- Firewall logic for neural data validation
- Programmatic access to the 14-layer model

---

## Installation

```bash
# From PyPI (recommended)
pip install oni-framework

# With visualization support
pip install oni-framework[viz]

# From source (for development)
git clone https://github.com/qikevinl/ONI.git
cd ONI/MAIN/oni-framework
pip install -e ".[dev]"
```

## Quick Start

### Calculate Coherence Score

**What it does:** Calculates a "trust score" (0 to 1) for a neural signal based on timing consistency, pathway reliability, and amplitude stability.

**What the data means:**
- `arrival_times` — When each signal pulse arrived (in seconds). In a real BCI, this would come from your device's timestamp data.
- `amplitudes` — How strong each pulse was (in microvolts). In a real BCI, this would be the measured voltage at each electrode.
- `reference_freq` — The expected brain oscillation frequency. 40 Hz (gamma waves) is used for cognitive processing signals.

```python
from oni import CoherenceMetric, calculate_cs

# Create metric with 40 Hz gamma reference
metric = CoherenceMetric(reference_freq=40.0)

# SAMPLE DATA (not real measurements!)
# In a real application, these would come from your BCI device
arrival_times = [0.0, 0.025, 0.050, 0.075, 0.100]  # seconds
amplitudes = [100, 98, 102, 99, 101]  # μV

# Calculate coherence
cs = metric.calculate(arrival_times, amplitudes)
print(f"Coherence Score: {cs:.3f}")

# Interpret the score
level, description = metric.interpret(cs)
print(f"{level}: {description}")
```

**What the score means:**
- **0.8 - 1.0:** High coherence — signal is consistent and trustworthy
- **0.5 - 0.8:** Medium coherence — some variance, may need verification
- **0.0 - 0.5:** Low coherence — signal is inconsistent, possibly tampered or noisy

### Use the Neural Firewall

**What it does:** Acts like a security guard for neural signals. It evaluates each signal and decides whether to ACCEPT, FLAG, or REJECT it based on coherence score and authentication status.

**Real-world analogy:** Like a firewall on your computer that blocks suspicious network traffic, this would block suspicious neural signals before they reach the brain or the computer interpreting brain signals.

**What the parameters mean:**
- `threshold_high` (0.6) — Signals above this coherence score are considered trustworthy
- `threshold_low` (0.3) — Signals below this are automatically rejected
- `amplitude_bounds` — Acceptable voltage range; anything outside is rejected (prevents over-powered attacks)
- `authenticated` — Whether the signal source has been verified (like a password check for the device)

```python
from oni import NeuralFirewall
from oni.firewall import Signal

# Create firewall with default thresholds
firewall = NeuralFirewall(
    threshold_high=0.6,
    threshold_low=0.3,
    amplitude_bounds=(0, 500),  # μV limits
)

# SAMPLE DATA (not real measurements!)
# In a real application, this would come from your BCI device
signal = Signal(
    arrival_times=[0.0, 0.025, 0.050],
    amplitudes=[100, 98, 102],
    authenticated=True,  # Device identity verified
)

# Filter the signal
result = firewall.filter(signal)

print(f"Decision: {result.decision.name}")  # ACCEPT, ACCEPT_FLAG, or REJECT
print(f"Coherence: {result.coherence:.3f}")
print(f"Alert Level: {result.alert_level.name}")
print(f"Reason: {result.reason}")
```

**Possible decisions:**
- **ACCEPT** — Signal is trusted, allow it through
- **ACCEPT_FLAG** — Signal is borderline, allow but log for review
- **REJECT** — Signal is untrusted or suspicious, block it

### Explore the 14-Layer Model

**What it does:** Provides a conceptual map of how information flows between the brain and a computer. Think of it like a building with 14 floors — signals travel up and down through each layer.

**Why 14 layers?** The traditional OSI network model has 7 layers. ONI extends this with 7 biological layers (brain side) + 1 bridge layer (where brain meets device) + 6 silicon layers (computer side) = 14 total.

**This is a reference model, not code that processes signals.** It helps researchers and engineers speak the same language when discussing where attacks might happen or where defenses should be placed.

```python
from oni import ONIStack

stack = ONIStack()

# Print the stack diagram
print(stack.ascii_diagram())

# Access specific layers
gateway = stack.layer(8)  # Neural Gateway — where brain meets device
print(f"Layer 8: {gateway.name}")
print(f"Function: {gateway.function}")
print(f"Attack surfaces: {gateway.attack_surfaces}")

# Iterate through biological layers (L1-L7, brain side)
for layer in stack.biological_layers():
    print(f"L{layer.number}: {layer.name}")
```

**Layer summary:**
- **L1-L7 (Silicon/OSI):** Standard networking layers — the computer's data movement
- **L8 (Neural Gateway):** The critical boundary where electrodes meet neurons — this is where the firewall operates
- **L9-L14 (Biology):** From signal processing to identity — the brain's neural processing

### Validate Scale-Frequency Relationship

**What it does:** Checks if a signal's frequency makes sense for its spatial scale. The brain follows a pattern: small structures (neurons) oscillate fast, large structures (brain regions) oscillate slowly.

**Real-world analogy:** A hummingbird's wings beat fast (small), an elephant's legs move slowly (large). If you saw an elephant moving its legs 100 times per second, you'd know something was wrong. This module catches similar "impossible" neural signals.

**The formula:** `frequency × spatial_scale ≈ constant (k)`

**Why this matters for security:** An attacker injecting fake signals might use the wrong frequency for the brain region they're targeting. This check catches that mismatch.

```python
from oni import ScaleFrequencyInvariant

sfi = ScaleFrequencyInvariant()

# SAMPLE CHECK (not a real measurement!)
# Ask: "Does a 40 Hz signal at 100 μm scale make biological sense?"
frequency = 40  # Hz (gamma wave)
spatial_scale = 1e-4  # meters (100 μm = size of a small neural cluster)

is_valid = sfi.validate(frequency, spatial_scale)
deviation = sfi.deviation(frequency, spatial_scale)

print(f"Valid: {is_valid}")
print(f"Deviation from expected: {deviation:.1%}")

# What frequency SHOULD we see at a given scale?
expected_f = sfi.expected_frequency(spatial_scale=1e-3)  # 1mm
print(f"Expected frequency at 1mm scale: {expected_f:.1f} Hz")

# Print the full hierarchy of scales and expected frequencies
print(sfi.hierarchy_report())
```

**What the hierarchy shows:**
| Scale | Size | Expected Frequency | Example |
|-------|------|-------------------|---------|
| Molecular | ~10 nm | Very fast | Ion channels |
| Cellular | ~10 μm | ~100-1000 Hz | Single neurons |
| Regional | ~10 mm | ~1-10 Hz | Brain regions |
| Whole-Brain | ~100 mm | <1 Hz | Global states |

## Detection Signatures

### Variance Components (σ²)

The Cₛ equation combines three variance measurements:

```python
from oni import CoherenceMetric

metric = CoherenceMetric(reference_freq=40.0)

# Get individual variance components for custom signatures
variances = metric.calculate_variances(arrival_times, amplitudes)
print(f"Phase variance (σ²φ): {variances.phase}")      # Timing attacks
print(f"Transport variance (σ²τ): {variances.transport}")  # Injection attacks
print(f"Gain variance (σ²γ): {variances.gain}")        # Amplitude attacks
```

**Default transport factors** (override for your hardware):
```python
DEFAULT_TRANSPORT_FACTORS = {
    'myelinated_axon': 0.999,       # Very reliable
    'unmyelinated_axon': 0.97,      # Slightly less reliable
    'synaptic_transmission': 0.85,  # Synapses sometimes fail
    'dendritic_integration': 0.90,  # Some signal loss
}
```

### Firewall Decision Matrix

| Cₛ Score | Authenticated | Decision | Action |
|----------|---------------|----------|--------|
| > 0.6 | Yes | `ACCEPT` | Allow signal |
| > 0.6 | No | `REJECT` | Block (auth required) |
| 0.3–0.6 | Yes | `FLAG` | Allow + log for review |
| 0.3–0.6 | No | `REJECT` | Block |
| < 0.3 | Any | `REJECT` | Block (anomaly detected) |

### Biological Plausibility Check

```python
from oni import ScaleFrequencyInvariant

sfi = ScaleFrequencyInvariant()

# Check if signal is biologically possible
# 40 Hz at 100μm scale (neural cluster) → valid
sfi.validate(frequency=40, spatial_scale=1e-4)  # True

# 500 Hz at 10cm scale (whole brain) → impossible
sfi.validate(frequency=500, spatial_scale=0.1)  # False → anomaly!

# Get anomaly score (0 = normal, 1 = impossible)
score = sfi.anomaly_score(frequency=500, spatial_scale=0.1)  # ~0.95
```

## Project Structure

```
oni-framework/
├── oni/
│   ├── __init__.py      # Package exports
│   ├── coherence.py     # Cₛ calculation
│   ├── layers.py        # 14-layer model
│   ├── firewall.py      # Signal filtering
│   └── scale_freq.py    # f × S ≈ k invariant
├── tests/
│   └── test_*.py        # Unit tests
├── pyproject.toml       # Package configuration
└── README.md            # This file
```

## API Reference

### `oni.CoherenceMetric`

- `calculate(arrival_times, amplitudes)` → Coherence score (0-1)
- `calculate_variances(...)` → Individual variance components
- `interpret(cs)` → (level, description) tuple

### `oni.NeuralFirewall`

- `filter(signal)` → FilterResult with decision
- `filter_batch(signals)` → List of FilterResults
- `get_stats()` → Filtering statistics
- `register_callback(level, fn)` → Alert callbacks

### `oni.ONIStack`

- `layer(n)` → Get layer by number (1-14)
- `biological_layers()` → L1-L7
- `silicon_layers()` → L9-L14
- `bridge_layer()` → L8 (Neural Gateway)
- `ascii_diagram()` → Visual representation

### `oni.ScaleFrequencyInvariant`

- `validate(frequency, scale)` → Boolean validity
- `deviation(frequency, scale)` → Fractional deviation
- `expected_frequency(scale)` → Predicted frequency
- `anomaly_score(frequency, scale)` → 0-1 anomaly score

## Documentation & Resources

**Full documentation on GitHub:**

| Resource | Description |
|----------|-------------|
| [ONI Framework Wiki](https://github.com/qikevinl/ONI/blob/main/MAIN/INDEX.md) | Central hub — navigation, dependencies, roadmap |
| [14-Layer Model Reference](https://github.com/qikevinl/ONI/blob/main/MAIN/oni-framework/ONI_LAYERS.md) | Complete layer specification with attack surfaces |
| [Coherence Metric](https://github.com/qikevinl/ONI/tree/main/MAIN/publications/coherence-metric/) | Technical document on Cₛ calculation |
| [Neural Firewall](https://github.com/qikevinl/ONI/tree/main/MAIN/publications/neural-firewall/) | Firewall architecture and decision matrix |
| [Scale-Frequency Invariant](https://github.com/qikevinl/ONI/tree/main/MAIN/publications/scale-frequency/) | The f × S ≈ k constraint |
| [Interactive Demos](https://qikevinl.github.io/ONI/visualizations/) | Browser-based learning tools |

**Related packages:**

| Package | Purpose | Install |
|---------|---------|---------|
| [oni-academy](https://pypi.org/project/oni-academy/) | Educational platform, tutorials | `pip install oni-academy` |
| [oni-tara](https://pypi.org/project/oni-tara/) | Security monitoring, attack simulation | `pip install oni-tara` |

## Contributing

Contributions welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

**Seeking input from:**
- Neuroscientists — Validate biological assumptions
- Security engineers — Identify attack vectors
- BCI researchers — Test against real data

## License

Apache License 2.0 - See [LICENSE](../../LICENSE)

## Citation

If you use this library in research, please cite:

```bibtex
@software{oni_framework,
  author = {Qi, Kevin L.},
  title = {ONI Framework: Security Library for Brain-Computer Interfaces},
  year = {2026},
  url = {https://github.com/qikevinl/ONI}
}
```
