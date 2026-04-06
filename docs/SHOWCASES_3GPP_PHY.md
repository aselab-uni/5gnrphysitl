# 3GPP-Inspired 5G NR PHY Showcases

This document extends the basic testcases and presents a set of deeper PHY showcases for teaching and guided lab work.

These showcases are built around 3GPP NR PHY ideas:

- OFDM numerology
- modulation and coding selection
- DMRS-assisted channel estimation
- fading and mobility effects
- reliability versus spectral efficiency

Important interpretation note:

- This project is **3GPP-inspired**, not fully standards-compliant.
- The PHY logic follows NR terminology and processing structure.
- Numerical thresholds in this prototype should be treated as **teaching outcomes of the current model**, not as conformance-grade NR reference values.

## How To Run the Showcase Bundle

Windows:

```cmd
run_showcases.bat
```

Linux/macOS:

```bash
chmod +x run_showcases.sh
./run_showcases.sh
```

Direct Python command:

```bash
python run_showcases.py --config configs/default.yaml --output-dir outputs/showcases
```

Generated outputs:

- `outputs/showcases/showcases.csv`
- `outputs/showcases/showcases.md`

## Showcase 1: Link Adaptation From Cell-Center to Cell-Edge

### 3GPP PHY idea

In 5G NR, the scheduler chooses an MCS based on channel quality. Good links can support higher-order QAM and higher coding rates. Weak links need more conservative settings.

This is the practical meaning of:

- CQI feedback
- MCS selection
- reliability versus throughput tradeoff

### Real-world situation

- **Cell-center UE**: strong received quality, usually more aggressive MCS is possible.
- **Cell-edge UE**: low SINR, aggressive MCS often fails, robust modulation is preferred.

### How to run

```bash
python run_showcases.py --config configs/default.yaml --output-dir outputs/showcases
```

Look for rows with `showcase_id = SC1`.

### Sample result from this repository

Cell-center at 20 dB:

| Modulation | Code rate | BER | BLER | Throughput |
| --- | ---: | ---: | ---: | ---: |
| QPSK | 0.50 | 0.0 | 0.0 | 2.05e6 |
| 16QAM | 0.50 | 0.0 | 0.0 | 2.05e6 |
| 64QAM | 0.70 | 0.0 | 0.0 | 2.05e6 |
| 256QAM | 0.80 | 0.0 | 0.0 | 2.05e6 |

Cell-edge at 0 dB:

| Modulation | Code rate | BER | BLER | Throughput |
| --- | ---: | ---: | ---: | ---: |
| QPSK | 0.50 | 0.0 | 0.0 | 2.05e6 |
| 16QAM | 0.50 | 0.00684 | 1.0 | 0 |
| 64QAM | 0.70 | 0.00488 | 1.0 | 0 |
| 256QAM | 0.80 | 0.08496 | 1.0 | 0 |

### Interpretation

- At the stronger operating point, all tested MCS-like settings decode successfully.
- At the weaker operating point, only the most robust setting survives in this prototype.
- This is exactly the logic behind link adaptation:
  use a conservative MCS when the channel is poor, and increase spectral efficiency only when the channel allows it.

### What students should discuss

1. Why does BLER matter more than BER for link adaptation?
2. Why can a tiny BER still be unacceptable when CRC fails?
3. Why should a scheduler prefer lower MCS near the cell edge?

## Showcase 2: 256QAM and the Cost of Spectral Efficiency

### 3GPP PHY idea

Higher-order QAM improves bits per symbol, but the minimum Euclidean distance between constellation points shrinks. This increases sensitivity to noise, residual equalization error, and phase distortions.

### Real-world situation

- High-throughput downlink near the gNB
- eMBB-style operating points
- situations where spectral efficiency is important but the channel must be clean enough

### How to run

```bash
python run_showcases.py --config configs/default.yaml --output-dir outputs/showcases
```

Look for rows with `showcase_id = SC2`.

### Sample result from this repository

| SNR (dB) | BER | BLER | EVM | Throughput |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.08496 | 1.0 | 0.66565 | 0 |
| 5 | 0.02441 | 1.0 | 0.37454 | 0 |
| 10 | 0.00195 | 1.0 | 0.21066 | 0 |
| 15 | 0.0 | 0.0 | 0.11847 | 2.05e6 |
| 20 | 0.0 | 0.0 | 0.06662 | 2.05e6 |

### Interpretation

- EVM improves smoothly with SNR.
- Reliable block decoding appears only after the SNR is high enough.
- This demonstrates a key PHY principle:
  a modulation order can look “almost fine” in BER terms and still be operationally unusable if BLER is high.

### What students should discuss

1. Why does 256QAM often need cleaner channels than QPSK?
2. Why does throughput stay at zero while BER is already quite small at 10 dB?
3. How would a practical gNB use CQI to avoid this regime?

## Showcase 3: DMRS and Channel Estimation in Fading Channels

### 3GPP PHY idea

NR inserts DMRS so the UE can estimate the channel on the allocated resources. Equalization quality depends strongly on estimation quality. In fast or selective fading, imperfect estimation raises EVM and can reduce the post-equalization SNR.

### Real-world situation

- Urban and indoor multipath
- fading channels where the receiver cannot assume perfect channel knowledge
- practical pilot-based equalization

### How to run

```bash
python run_showcases.py --config configs/default.yaml --output-dir outputs/showcases
```

Look for rows with `showcase_id = SC3`.

### Sample result from this repository

Pedestrian profile at 15 dB:

| Estimation mode | EVM | Estimated SNR (dB) |
| --- | ---: | ---: |
| Perfect CE | 0.21062 | 13.53 |
| DMRS LS | 0.25694 | 11.80 |

Vehicular profile at 15 dB:

| Estimation mode | EVM | Estimated SNR (dB) |
| --- | ---: | ---: |
| Perfect CE | 0.18893 | 14.47 |
| DMRS LS | 0.26436 | 11.56 |

Urban LOS profile at 15 dB:

| Estimation mode | EVM | Estimated SNR (dB) |
| --- | ---: | ---: |
| Perfect CE | 0.22851 | 12.82 |
| DMRS LS | 0.29889 | 10.49 |

### Interpretation

- Perfect channel knowledge is always the upper bound.
- DMRS-based estimation in the current prototype is still good enough to decode these cases, but the equalized symbol quality is worse.
- The gap between perfect CE and DMRS LS is a teaching proxy for:
  pilot density, interpolation quality, and estimator robustness.

### What students should discuss

1. Why does channel estimation error show up as EVM degradation?
2. Why can the same nominal SNR still produce different post-equalization SNR?
3. In a more realistic system, when would we need denser DMRS or better interpolation?

## Showcase 4: Numerology and Mobility

### 3GPP PHY idea

NR supports multiple numerologies. Larger subcarrier spacing shortens the OFDM symbol duration, which can improve tolerance to channel variation over one symbol. This is one reason why numerology matters in mobility and higher-frequency operation.

### Real-world situation

- vehicular mobility
- rapidly varying channels
- different deployment options in FR1/FR2-inspired thinking

### How to run

```bash
python run_showcases.py --config configs/default.yaml --output-dir outputs/showcases
```

Look for rows with `showcase_id = SC4`.

### Sample result from this repository

At 15 dB with vehicular fading and 200 Hz Doppler:

| Numerology | SCS (kHz) | EVM | Estimated SNR (dB) | Throughput |
| --- | ---: | ---: | ---: | ---: |
| mu0 | 15 | 0.28984 | 10.76 | 1.03e6 |
| mu1 | 30 | 0.24200 | 12.32 | 2.05e6 |
| mu2 | 60 | 0.25124 | 11.99 | 4.10e6 |

### Interpretation

- In this prototype, `mu1` gives the best EVM among the tested cases.
- `mu0` is more sensitive in this mobility setting because symbols are longer.
- `mu2` does not automatically dominate, which is also realistic pedagogically:
  numerology is a tradeoff, not a universal “bigger is always better” rule.

### Model note

- These results are **illustrative**, not 3GPP reference curves.
- Throughput differences here also reflect the configured bandwidth/resource scaling used in the showcase.

### What students should discuss

1. Why does shorter symbol duration help under Doppler?
2. Why can a larger SCS also change bandwidth and other resource assumptions?
3. Why should we avoid interpreting numerology results from a simplified simulator too literally?

## Showcase 5: Lab-Clean Link vs Mobility-Stressed Link

### 3GPP PHY idea

PHY robustness is not evaluated only in clean AWGN conditions. Real NR links must tolerate:

- multipath
- Doppler
- CFO/STO
- estimation imperfections

### Real-world situation

- comparing a controlled lab setup with a realistic mobile radio channel
- moving from a classroom “works on AWGN” demo to a research-grade link stress test

### How to run

Baseline:

```bash
python main.py --config configs/default.yaml
```

Stress case:

```bash
python main.py --config configs/default.yaml --override configs/scenario_vehicular.yaml
```

or run the bundled showcase command and inspect `showcase_id = SC5`.

### Sample result from this repository

| Scenario | BER | BLER | EVM | Throughput | Estimated SNR (dB) |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_awgn | 0.0 | 0.0 | 0.00667 | 2.05e6 | 43.51 |
| vehicular_stress | 0.73633 | 1.0 | 2.00057 | 0 | -6.02 |

### Interpretation

- This pair is a strong reminder that a PHY chain validated in AWGN is only the beginning.
- In the stressed scenario, decoding collapses and throughput becomes zero.
- This is why standard-inspired PHY studies must always test:
  clean reference cases
- and:
  realistic impairment cases

### What students should discuss

1. Which impairment is likely most harmful here: Doppler, delay spread, CFO, or their combination?
2. Why is throughput often the easiest KPI to explain to a non-PHY audience?
3. What receiver improvements would you try first: synchronization, channel estimation, or equalization?

## Suggested Teaching Sequence

1. Start with Showcase 5 baseline to verify that the simulator is healthy.
2. Move to Showcase 1 to motivate MCS selection and cell-center versus cell-edge behavior.
3. Use Showcase 2 to connect constellation density with BLER.
4. Use Showcase 3 to explain why DMRS exists and why equalization depends on CE quality.
5. Use Showcase 4 to introduce numerology and mobility.
6. Return to Showcase 5 stress mode and ask students how they would redesign the receiver.

## Best-Practice Message for Students

When using a simulator for PHY learning, always ask three questions:

1. What physical principle is this result demonstrating?
2. What part is specific to this implementation?
3. What would have to change to move from a teaching model to a conformance-grade NR PHY?
