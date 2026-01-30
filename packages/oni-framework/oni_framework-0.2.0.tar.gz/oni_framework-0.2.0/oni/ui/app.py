"""
ONI Framework Interactive UI
============================

A Streamlit-based interface for learning and exploring the ONI Framework.
Designed for researchers, developers, and non-technical stakeholders.

Launch with:
    oni ui
    # or
    streamlit run oni/ui/app.py
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="ONI Framework",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: 1px solid #334155;
    }
    .metric-box {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .code-example {
        background: #0f172a;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Sidebar navigation
    page = render_sidebar()

    # Render selected page
    if page == "Home":
        render_home()
    elif page == "What is ONI?":
        render_what_is_oni()
    elif page == "The 14 Layers":
        render_layers()
    elif page == "Coherence Metric":
        render_coherence()
    elif page == "Neural Firewall":
        render_firewall()
    elif page == "Privacy Tools":
        render_privacy()
    elif page == "Threat Detection":
        render_threats()
    elif page == "Code Examples":
        render_examples()
    elif page == "For Developers":
        render_developers()


def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.markdown("## 🧠 ONI Framework")

        try:
            from oni import __version__
            st.caption(f"Version {__version__}")
        except:
            st.caption("Version unknown")

        st.markdown("---")

        page = st.radio(
            "Navigate",
            [
                "Home",
                "What is ONI?",
                "The 14 Layers",
                "Coherence Metric",
                "Neural Firewall",
                "Privacy Tools",
                "Threat Detection",
                "Code Examples",
                "For Developers",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        st.markdown("""
        **Resources**
        - [GitHub](https://github.com/qikevinl/ONI)
        - [Documentation](https://qikevinl.github.io/ONI/)
        - [PyPI](https://pypi.org/project/oni-framework/)
        """)

        st.markdown("---")
        st.caption("Apache 2.0 License")

    return page


def render_home():
    """Render the home page."""
    st.markdown('<p class="main-header">ONI Framework</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Neural Security for Brain-Computer Interfaces</p>', unsafe_allow_html=True)

    # Mission statement
    st.info("""
    **Our Mission:** Build the security standard for brain-computer interfaces
    *before* the first satisfying exploit of the human mind — because the brain
    deserves the same protection we give our networks.
    """)

    st.markdown("---")

    # What you get
    st.markdown("### What You Get")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🎯 Signal Trust")
        st.markdown("""
        Calculate **coherence scores** (0-1) to measure
        how trustworthy a neural signal is based on
        timing, amplitude, and pathway reliability.
        """)

    with col2:
        st.markdown("#### 🛡️ Neural Firewall")
        st.markdown("""
        **Accept or reject** signals based on trust
        scores and authentication. Like a network
        firewall, but for brain-computer interfaces.
        """)

    with col3:
        st.markdown("#### 🔒 Privacy Tools")
        st.markdown("""
        **Anonymize neural data** by stripping
        privacy-sensitive patterns. Calculate
        information leakage risk scores.
        """)

    st.markdown("---")

    # Quick stats
    st.markdown("### Framework at a Glance")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Security Layers", "14")
    with col2:
        st.metric("Threat Patterns", "21")
    with col3:
        st.metric("Dependencies", "0")
    with col4:
        st.metric("Research Papers", "12+")

    st.markdown("---")

    # Quick start
    st.markdown("### Quick Start")
    st.code("""
pip install oni-framework

# In Python:
from oni import CoherenceMetric

metric = CoherenceMetric(reference_freq=40.0)
trust_score = metric.calculate(
    arrival_times=[0.0, 0.025, 0.050],
    amplitudes=[100, 98, 102]
)
print(f"Signal trust: {trust_score:.2f}")
    """, language="python")


def render_what_is_oni():
    """Render the 'What is ONI?' page."""
    st.markdown("## What is ONI?")

    st.markdown("""
    **ONI (Organic Neural Interface)** is a security framework for brain-computer interfaces.

    ### The Problem

    Brain-computer interfaces (BCIs) are being implanted in humans today:
    - **Neuralink** implanted its first patient in 2024
    - **Synchron** is in FDA clinical trials
    - **Blackrock Neurotech** has been in human brains since 2004

    **But there's no security standard.**

    The brain evolved no mechanism to distinguish real from injected signals.
    If a signal's amplitude, frequency, and timing fall within biological norms,
    the brain processes it as real.

    ### The Solution

    ONI provides a **14-layer security model** that extends the familiar OSI
    networking stack into the biological domain:

    - **L1-L7 (Silicon):** Standard OSI networking layers
    - **L8 (Neural Gateway):** The firewall layer — where electrodes meet neurons
    - **L9-L14 (Biology):** Neural and cognitive layers

    ### Who It's For

    | Audience | Use Case |
    |----------|----------|
    | **Researchers** | Academic teams studying BCI security |
    | **Developers** | Engineers building neural interfaces |
    | **Regulators** | FDA, FCC, policy makers |
    | **Security Teams** | Red teams, pentesters |

    ### Built On Research

    ONI integrates work from 12+ universities:
    - **Kohno et al. (2009):** Coined "neurosecurity", CIA threat model
    - **Bonaci et al. (2015):** BCI Anonymizer patent
    - **Yuste et al. (2017):** Neurorights framework
    - **Ienca & Andorno (2017):** Cognitive liberty principles
    """)


def render_layers():
    """Render the 14-layer model page."""
    st.markdown("## The 14-Layer ONI Model")

    st.markdown("""
    ONI extends the OSI networking model with neural-specific layers.
    """)

    try:
        from oni import ONIStack
        stack = ONIStack()

        # Visual representation
        st.markdown("### Layer Stack")

        # Biology layers (top)
        st.markdown("#### 🧬 Biology (L9-L14)")
        for layer in reversed(list(stack.biological_layers())):
            with st.expander(f"**L{layer.number}** — {layer.name}"):
                st.markdown(f"**Function:** {layer.function}")
                if hasattr(layer, 'attack_surfaces') and layer.attack_surfaces:
                    st.markdown(f"**Attack Surfaces:** {', '.join(layer.attack_surfaces)}")

        # Bridge layer
        st.markdown("#### 🌉 Bridge (L8)")
        gateway = stack.layer(8)
        with st.expander(f"**L8** — {gateway.name} (FIREWALL LAYER)", expanded=True):
            st.markdown(f"**Function:** {gateway.function}")
            st.warning("This is where the Neural Firewall operates — the critical trust boundary between silicon and biology.")

        # Silicon layers (bottom)
        st.markdown("#### 💻 Silicon (L1-L7)")
        for layer in reversed(list(stack.silicon_layers())):
            with st.expander(f"**L{layer.number}** — {layer.name}"):
                st.markdown(f"**Function:** {layer.function}")

    except Exception as e:
        st.error(f"Error loading layer model: {e}")

    st.markdown("---")

    st.markdown("""
    ### Key Insight

    - **OSI (L1-L7)** answers: *How does data move?*
    - **ONI (L8-L14)** answers: *Should it move, can it be trusted, and what does it mean?*
    """)


def render_coherence():
    """Render the coherence metric page."""
    st.markdown("## Coherence Metric (Cₛ)")

    st.markdown("""
    The **Coherence Score** measures how trustworthy a neural signal is.

    ### The Formula

    ```
    Cₛ = f(σ²φ, σ²τ, σ²γ)
    ```

    Where:
    - **σ²φ (Phase variance):** Is the signal arriving on time?
    - **σ²τ (Transport variance):** Is the pathway reliable?
    - **σ²γ (Gain variance):** Is the amplitude stable?

    ### Score Interpretation

    | Score | Level | Meaning |
    |-------|-------|---------|
    | 0.8 - 1.0 | High | Signal is consistent and trustworthy |
    | 0.5 - 0.8 | Medium | Some variance, may need verification |
    | 0.0 - 0.5 | Low | Signal is inconsistent, possibly tampered |
    """)

    st.markdown("---")

    st.markdown("### Try It")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Signal Parameters**")
        ref_freq = st.slider("Reference Frequency (Hz)", 1, 100, 40)
        timing_variance = st.slider("Timing Jitter", 0.0, 1.0, 0.1)
        amplitude_variance = st.slider("Amplitude Variance", 0.0, 1.0, 0.1)

    with col2:
        try:
            from oni import CoherenceMetric
            import random

            # Generate sample signal with specified variance
            base_interval = 1.0 / ref_freq
            times = [0.0]
            amps = [100]

            for i in range(4):
                # Add timing jitter
                jitter = (random.random() - 0.5) * 2 * timing_variance * base_interval
                times.append(times[-1] + base_interval + jitter)

                # Add amplitude variance
                amp_jitter = (random.random() - 0.5) * 2 * amplitude_variance * 50
                amps.append(100 + amp_jitter)

            metric = CoherenceMetric(reference_freq=float(ref_freq))
            cs = metric.calculate(times, amps)
            level, description = metric.interpret(cs)

            st.markdown("**Result**")
            st.metric("Coherence Score", f"{cs:.3f}")
            st.info(f"**{level}:** {description}")

        except Exception as e:
            st.error(f"Error: {e}")


def render_firewall():
    """Render the neural firewall page."""
    st.markdown("## Neural Firewall")

    st.markdown("""
    The **Neural Firewall** operates at L8 (Neural Gateway), deciding whether
    to allow signals to pass between the brain and the computer.

    ### Decision Matrix

    | Coherence | Authenticated | Decision |
    |-----------|---------------|----------|
    | High (>0.6) | Yes | ✅ ACCEPT |
    | High (>0.6) | No | ❌ REJECT |
    | Medium (0.3-0.6) | Yes | ⚠️ ACCEPT + FLAG |
    | Medium (0.3-0.6) | No | ❌ REJECT |
    | Low (<0.3) | Any | ❌ REJECT |

    ### How It Works

    1. Signal arrives at the Neural Gateway
    2. Coherence score is calculated
    3. Authentication is checked
    4. Decision: ACCEPT, REJECT, or ACCEPT_FLAG
    5. Alert callbacks triggered if needed
    """)

    st.markdown("---")

    st.markdown("### Simulate")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Firewall Settings**")
        threshold_high = st.slider("High Threshold", 0.5, 0.9, 0.6)
        threshold_low = st.slider("Low Threshold", 0.1, 0.5, 0.3)
        authenticated = st.checkbox("Signal Authenticated", value=True)

    with col2:
        st.markdown("**Signal Quality**")
        signal_quality = st.select_slider(
            "Quality",
            options=["Very Low", "Low", "Medium", "High", "Very High"],
            value="High"
        )

    # Map quality to coherence
    quality_map = {
        "Very Low": ([0.0, 0.1, 0.15], [100, 30, 180]),
        "Low": ([0.0, 0.03, 0.07], [100, 70, 130]),
        "Medium": ([0.0, 0.026, 0.052], [100, 85, 115]),
        "High": ([0.0, 0.025, 0.050], [100, 95, 105]),
        "Very High": ([0.0, 0.025, 0.050], [100, 99, 101]),
    }

    times, amps = quality_map[signal_quality]

    try:
        from oni import NeuralFirewall
        from oni.firewall import Signal

        firewall = NeuralFirewall(
            threshold_high=threshold_high,
            threshold_low=threshold_low,
        )

        signal = Signal(
            arrival_times=times,
            amplitudes=amps,
            authenticated=authenticated,
        )

        result = firewall.filter(signal)

        st.markdown("---")
        st.markdown("### Result")

        col1, col2, col3 = st.columns(3)

        with col1:
            decision_color = {
                "ACCEPT": "🟢",
                "REJECT": "🔴",
                "ACCEPT_FLAG": "🟡",
            }
            st.metric("Decision", f"{decision_color.get(result.decision.name, '')} {result.decision.name}")

        with col2:
            st.metric("Coherence", f"{result.coherence:.3f}")

        with col3:
            st.metric("Alert Level", result.alert_level.name)

        st.info(f"**Reason:** {result.reason}")

    except Exception as e:
        st.error(f"Error: {e}")


def render_privacy():
    """Render the privacy tools page."""
    st.markdown("## Privacy Tools")

    st.markdown("""
    ONI includes privacy-preserving tools based on the **BCI Anonymizer** patent
    (Chizeck & Bonaci, 2014).

    ### Why Privacy Matters

    Neural signals can reveal:
    - **P300 (Surprise Response):** Whether you recognize something
    - **N170 (Face Recognition):** Who you know
    - **ERN (Error Related):** Your mistakes and doubts
    - **LRP (Motor Preparation):** Your intended actions

    An attacker could extract:
    - Bank PINs (via P300 probing)
    - Known faces (via N170)
    - Lies and deception (via ERN)

    ### BCI Anonymizer

    Strips privacy-sensitive event-related potentials (ERPs) before
    data leaves the device.

    ### Privacy Score Calculator

    Quantifies how much private information a signal might leak.
    """)

    st.markdown("---")

    st.markdown("### Calculate Privacy Risk")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Signal Properties**")
        has_p300 = st.checkbox("Contains P300 (Surprise)", value=True)
        has_n170 = st.checkbox("Contains N170 (Face)", value=False)
        has_ern = st.checkbox("Contains ERN (Error)", value=False)
        snr = st.slider("Signal-to-Noise Ratio (dB)", 0, 40, 20)
        duration = st.slider("Recording Duration (seconds)", 1, 300, 60)

    with col2:
        try:
            from oni import PrivacyScoreCalculator, ERPType

            erps = []
            if has_p300:
                erps.append(ERPType.P300)
            if has_n170:
                erps.append(ERPType.N170)
            if has_ern:
                erps.append(ERPType.ERN)

            calculator = PrivacyScoreCalculator()
            result = calculator.calculate(
                detected_erps=erps,
                signal_snr=float(snr),
                recording_duration=float(duration),
            )

            st.markdown("**Risk Assessment**")
            st.metric("Privacy Risk Score", f"{result.score:.2f}")

            if result.score < 0.3:
                st.success(f"**Low Risk:** {result.interpretation}")
            elif result.score < 0.6:
                st.warning(f"**Medium Risk:** {result.interpretation}")
            else:
                st.error(f"**High Risk:** {result.interpretation}")

        except Exception as e:
            st.error(f"Error: {e}")


def render_threats():
    """Render the threat detection page."""
    st.markdown("## Threat Detection")

    st.markdown("""
    ONI implements the **Kohno Threat Model** (2009) — the foundational
    taxonomy for BCI security threats.

    ### The CIA Triad for BCIs

    | Threat Type | CIA Property | What It Means |
    |-------------|--------------|---------------|
    | **Alteration** | Integrity | Modifying neural signals |
    | **Blocking** | Availability | Preventing signals from reaching destination |
    | **Eavesdropping** | Confidentiality | Unauthorized access to neural data |

    ### Example Attack Patterns

    | Attack | Type | ONI Layer | Impact |
    |--------|------|-----------|--------|
    | Signal Injection | Alteration | L8-L9 | False sensations |
    | Neural DoS | Blocking | L8 | Device lockout |
    | P300 Probing | Eavesdropping | L13 | Extracting memories |
    | Motor Override | Alteration | L13 | Forced movement |
    """)

    st.markdown("---")

    st.markdown("### Threat Classification")

    try:
        from oni import KohnoThreatModel, ThreatType

        model = KohnoThreatModel()

        for threat_type in ThreatType:
            info = model.get_threat_info(threat_type)
            with st.expander(f"**{threat_type.name}** — {info['cia_property']}"):
                st.markdown(f"**Description:** {info['description']}")
                st.markdown(f"**Target Layers:** {info['target_layers']}")
                st.markdown(f"**Countermeasures:** {info['countermeasures']}")

    except Exception as e:
        st.error(f"Error: {e}")


def render_examples():
    """Render code examples page."""
    st.markdown("## Code Examples")

    st.markdown("### 1. Calculate Signal Trust Score")
    st.code("""
from oni import CoherenceMetric

# Create metric with 40Hz gamma reference
metric = CoherenceMetric(reference_freq=40.0)

# Your signal data (from BCI device)
arrival_times = [0.0, 0.025, 0.050, 0.075, 0.100]
amplitudes = [100, 98, 102, 99, 101]

# Calculate coherence
cs = metric.calculate(arrival_times, amplitudes)
print(f"Trust score: {cs:.3f}")

# Interpret
level, description = metric.interpret(cs)
print(f"{level}: {description}")
    """, language="python")

    st.markdown("### 2. Filter Signals with Firewall")
    st.code("""
from oni import NeuralFirewall
from oni.firewall import Signal

# Create firewall with thresholds
firewall = NeuralFirewall(
    threshold_high=0.6,  # Above this = trusted
    threshold_low=0.3,   # Below this = rejected
)

# Create a signal
signal = Signal(
    arrival_times=[0.0, 0.025, 0.050],
    amplitudes=[100, 98, 102],
    authenticated=True,
)

# Filter it
result = firewall.filter(signal)
print(f"Decision: {result.decision.name}")
print(f"Coherence: {result.coherence:.3f}")
print(f"Reason: {result.reason}")
    """, language="python")

    st.markdown("### 3. Anonymize Neural Data")
    st.code("""
from oni import BCIAnonymizer

# Create anonymizer
anonymizer = BCIAnonymizer()

# Your raw signal
raw_signal = get_signal_from_device()

# Anonymize (strips P300, N170, etc.)
clean_signal = anonymizer.process(raw_signal)

# Safe to share
save_to_research_database(clean_signal)
    """, language="python")

    st.markdown("### 4. Classify Threats")
    st.code("""
from oni import NeurosecurityFirewall

# Create combined firewall (coherence + threat detection)
firewall = NeurosecurityFirewall()

# Analyze signal
result = firewall.analyze(signal)

# Check threat classification
if result.threat_type:
    print(f"Threat: {result.threat_type.name}")
    print(f"CIA Impact: {result.cia_property}")
    print(f"Recommended Action: {result.action}")
    """, language="python")

    st.markdown("### 5. Explore the 14-Layer Model")
    st.code("""
from oni import ONIStack

stack = ONIStack()

# Get the firewall layer
gateway = stack.layer(8)
print(f"L8: {gateway.name}")
print(f"Function: {gateway.function}")

# Iterate through biological layers
for layer in stack.biological_layers():
    print(f"L{layer.number}: {layer.name}")

# Print ASCII diagram
print(stack.ascii_diagram())
    """, language="python")


def render_developers():
    """Render the developers page."""
    st.markdown("## For Developers")

    st.markdown("""
    ### Installation Options

    ```bash
    # Core only (zero dependencies)
    pip install oni-framework

    # With interactive UI
    pip install oni-framework[ui]

    # Everything
    pip install oni-framework[all]
    ```

    ### Package Structure

    ```
    oni/
    ├── __init__.py          # Main exports
    ├── coherence.py         # Cₛ calculation
    ├── firewall.py          # Signal filtering
    ├── layers.py            # 14-layer model
    ├── scale_freq.py        # f × S ≈ k validation
    ├── cli.py               # Command-line interface
    ├── ui/                   # Streamlit UI
    └── neurosecurity/
        ├── threats.py       # Kohno threat model
        ├── firewall.py      # Neurosecurity firewall
        ├── anonymizer.py    # BCI Anonymizer
        ├── privacy_score.py # Privacy risk scoring
        └── consent.py       # Consent management
    ```

    ### CLI Commands

    ```bash
    oni ui       # Launch interactive UI
    oni info     # Show framework summary
    oni demo     # Run quick demo
    oni version  # Show version
    ```

    ### Integration with Hardware

    ONI is a framework, not a measurement tool. To use with real BCIs:

    1. Get signal data from your device (OpenBCI, Neuralink, etc.)
    2. Pass timestamps and amplitudes to ONI
    3. Use the results to make security decisions

    Example with OpenBCI:
    ```python
    from oni import CoherenceMetric, NeuralFirewall
    from openbci import OpenBCIBoard  # hypothetical

    board = OpenBCIBoard()
    metric = CoherenceMetric(reference_freq=10.0)  # Alpha
    firewall = NeuralFirewall()

    def on_sample(sample):
        # Get timestamps and amplitudes from sample
        times = sample.timestamps
        amps = sample.channel_data[0]

        # Calculate trust
        cs = metric.calculate(times, amps)

        # Make decision
        if cs < 0.3:
            print("WARNING: Low coherence signal detected!")
    ```

    ### Contributing

    - GitHub: https://github.com/qikevinl/ONI
    - Issues: https://github.com/qikevinl/ONI/issues

    We welcome contributions from:
    - Neuroscientists (validate biological assumptions)
    - Security engineers (identify attack vectors)
    - BCI researchers (test against real data)
    """)


if __name__ == "__main__":
    main()
