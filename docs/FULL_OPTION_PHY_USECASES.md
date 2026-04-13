# Full-Option PHY Pipeline Use Cases

## Scope

This document organizes practical use cases for a `full-option` 5G NR PHY pipeline. The intent is to bridge:

- the current `3GPP-inspired` software-only platform,
- the future full-option pipeline that includes `Layer Mapping`, `Precoding`, `RF front-end`, `Remove CP`, `Resource Element Extraction`, `Layer Recovery / De-precoding`, `Descrambling`, `Rate Recovery`, and explicit `Soft LLR` inspection,
- and the concrete teaching or research question each experiment should answer.

The document is written for a `software-in-the-loop (SITL)` environment. No SDR hardware is assumed.

## Full-Option Pipeline Reference

```mermaid
flowchart LR
    A["Bits / Source Payload"]
    B["TB Formation + CRC"]
    C["Channel Coding"]
    D["Rate Matching"]
    E["Scrambling"]
    F["QAM Mapping"]
    G["Layer Mapping"]
    H["Precoding"]
    I["RE Mapping + DMRS"]
    J["IFFT + CP + TX RF Front-End"]
    K["Wireless Channel + Impairments"]
    L["RX RF Front-End + Sync"]
    M["Remove CP + FFT"]
    N["Resource Element Extraction"]
    O["Channel Estimation"]
    P["Equalization"]
    Q["Layer Recovery / De-precoding"]
    R["Soft Demapping"]
    S["Descrambling"]
    T["Rate Recovery"]
    U["Soft LLR Buffer"]
    V["Decoding + CRC Check"]
    W["Recovered Bits / File"]

    A-->B-->C-->D-->E-->F-->G-->H-->I-->J-->K-->L-->M-->N-->O-->P-->Q-->R-->S-->T-->U-->V-->W
```

## Use Case Matrix

| ID | Use case | Main objective | Most important blocks | Main KPI |
| --- | --- | --- | --- | --- |
| UC-01 | End-to-end PHY teaching demo | Explain the full chain from bits to CRC check | Entire pipeline | BER, BLER, EVM |
| UC-02 | Multi-slot timeline demo | Show time evolution across slots and frames | Sync, FFT, CE, EQ | Slot-wise BER/BLER |
| UC-03 | Text vs image file transfer | Show application-level consequence of PHY errors | Decoder, CRC, file reassembly | File success, chunks failed |
| UC-04 | Perfect vs realistic receiver | Quantify optimistic vs realistic assumptions | Sync, CE, EQ | BER, BLER, CE MSE |
| UC-05 | Modulation and MCS comparison | Compare robustness vs spectral efficiency | Mapping, demapping, decoder | Throughput, BLER |
| UC-06 | DMRS / CE / EQ study | Measure estimation quality impact | RE extraction, CE, EQ | EVM, CE MSE, BER |
| UC-07 | Sync impairment study | Study timing/CFO sensitivity | RX front-end, sync, CP removal | Sync error, BER |
| UC-08 | RF impairment study | Study phase noise, IQ imbalance, quantization | TX/RX RF front-end | EVM, BER |
| UC-09 | Channel profile comparison | Compare LOS/NLOS/fading environments | Channel, CE, EQ | BER, BLER, estimated SNR |
| UC-10 | Doppler mobility study | Evaluate mobility and tracking stress | Channel, sync, CE | BER, EVM |
| UC-11 | Single-layer vs multi-layer MIMO | Evaluate spatial multiplexing tradeoffs | Layer mapping, precoding, de-precoding | Throughput, BLER |
| UC-12 | Decoder-input quality study | Explain why decoder succeeds or fails | Demapper, descrambling, rate recovery, soft LLR | LLR quality, BER |

## Detailed Use Cases

### UC-01: End-to-End PHY Teaching Demo

**Goal**

Explain the role of every block in the PHY chain, using a clean scenario that minimizes confusion from channel artifacts.

**Recommended setup**

- Modulation: `QPSK`
- Channel: `AWGN`
- SNR: `20 to 40 dB`
- Perfect sync: `On`
- Perfect CE: `On`
- Capture slots: `1 to 3`

**Artifacts to emphasize**

- payload bits
- CRC-attached bits
- coded bits
- scrambled bits
- constellation
- resource grid and DMRS
- OFDM waveform
- estimated channel
- decoder output and CRC status

**Expected conclusion**

Students should understand that each block changes either:

- the protection applied to the information,
- the representation domain of the signal,
- or the receiver’s ability to invert channel distortion.

### UC-02: Multi-Slot Timeline Demo

**Goal**

Use the `Frame / Slot / Symbol` scrubbers to show that PHY behavior evolves over time rather than existing as one frozen slot snapshot.

**Recommended setup**

- Capture slots: `12` or `20`
- Channel: `AWGN` for clean baseline, then `Rayleigh` for realism
- Perfect sync: `Off`
- Perfect CE: `Off`

**Artifacts to emphasize**

- stage title `Frame x / Slot y`
- playback across slot boundaries
- per-slot constellation
- per-slot estimated channel response

**Expected conclusion**

Students should see that time evolution matters. The receiver is not solving one slot once; it repeatedly solves a stream of slots under changing channel and impairment conditions.

### UC-03: Text vs Image File Transfer

**Goal**

Show why application-level reliability depends not only on per-block BER/BLER but also on payload size and the number of transport blocks.

**Recommended setup**

- Text sample: `input/sample_message.txt`
- Image sample: `input/sample_image.png`
- Modulation: `QPSK`
- Channel: `AWGN`
- SNR sweep: `0, 2, 4, 6, 8, 10, 20, 40 dB`
- Perfect sync / CE: compare `On` vs `Off`

**Artifacts to emphasize**

- `File Source + Packaging`
- `File Reassembly + Write`
- chunk pass/fail counts
- restored RX file names with SNR labels

**Expected conclusion**

The image fails earlier than the text because it spans far more PHY chunks. File transfer success is therefore an `all-or-nothing` event at application level.

### UC-04: Perfect vs Realistic Receiver

**Goal**

Quantify how much performance is artificially improved when `perfect_sync` and `perfect_channel_estimation` are enabled.

**Recommended setup**

Run each scenario twice:

- Case A: `Perfect sync = On`, `Perfect CE = On`
- Case B: `Perfect sync = Off`, `Perfect CE = Off`

Use the same SNR, channel model, and modulation.

**Artifacts to emphasize**

- timing correlation
- CFO trace
- estimated channel grid
- equalized constellation
- soft LLR histogram

**Expected conclusion**

This use case is important for teaching model honesty. Students should learn to separate:

- a convenient educational assumption,
- from a realistic receiver burden.

### UC-05: Modulation and MCS Comparison

**Goal**

Compare robustness against spectral efficiency.

**Recommended setup**

- Modulation: `QPSK`, `16QAM`, `64QAM`, `256QAM`
- Code rate: fixed first, then sweep
- Channel: `AWGN`, later `Rayleigh`
- SNR sweep: broad enough to show failure and success regions

**Artifacts to emphasize**

- mapping table
- pre/post-channel constellation
- LLR histogram
- KPI bars

**Expected conclusion**

Higher-order modulation is more spectrally efficient but more sensitive to impairment and noise. The LLR distribution becomes a useful explanation for why the decoder eventually fails.

### UC-06: DMRS / Channel Estimation / Equalization Study

**Goal**

Explain how pilot structure enables data recovery and how CE error propagates into decoding.

**Recommended setup**

- Channel: `Rayleigh` or `Rician`
- Delay spread: non-zero
- Perfect CE: `Off`
- Compare equalizers if available

**Artifacts to emphasize**

- allocation map
- DMRS mask
- estimated channel grid
- equalizer gain
- pre/post-EQ constellation

**Expected conclusion**

Bad channel estimation does not only make the channel plot ugly; it directly damages the equalizer output and then the decoder input.

### UC-07: Synchronization Impairment Study

**Goal**

Study failure mechanisms from timing offset, CFO, and related impairment.

**Recommended setup**

- Perfect sync: `Off`
- sweep `CFO`, `STO`, and optionally `phase_noise_std`
- use `QPSK` first for easier interpretation

**Artifacts to emphasize**

- timing correlation
- CFO estimate trace
- corrected waveform
- RX grid quality

**Expected conclusion**

Synchronization errors appear early in the chain but poison everything downstream. This is one of the clearest examples of error propagation in PHY.

### UC-08: RF Impairment Study

**Goal**

Evaluate how practical front-end imperfections manifest in a software-only baseband/RF model.

**Recommended setup**

- phase noise sweep
- IQ imbalance sweep
- optional quantization model once implemented
- compare with and without perfect sync/CE

**Artifacts to emphasize**

- TX/RX waveform
- TX/RX spectrum
- constellation spreading
- LLR degradation

**Expected conclusion**

Not all performance loss is caused by the propagation channel. Front-end imperfection changes the quality of the observations before the decoder ever sees them.

### UC-09: Channel Profile Comparison

**Goal**

Compare nominally identical PHY settings under different propagation conditions.

**Recommended setup**

- profiles: `static_near`, `pedestrian`, `vehicular`, `urban_los`, `urban_nlos`
- same modulation and code rate
- same nominal SNR for first comparison

**Artifacts to emphasize**

- impulse response
- frequency response
- channel estimate grid
- post-EQ constellation

**Expected conclusion**

The same nominal SNR can still produce very different link quality when the channel structure changes.

### UC-10: Doppler Mobility Study

**Goal**

Stress the pipeline with mobility and show why tracking matters across slots.

**Recommended setup**

- channel model: `Rayleigh` or `Rician`
- Doppler sweep: low, medium, high
- Capture slots: `10+`
- Perfect sync / CE: `Off`

**Artifacts to emphasize**

- slot-by-slot playback
- channel estimate drift
- changing constellation quality over time

**Expected conclusion**

Mobility is fundamentally a time-variation problem, so single-slot inspection is insufficient. Multi-slot playback becomes essential here.

### UC-11: Single-Layer vs Multi-Layer MIMO

**Goal**

Evaluate the impact of `Layer Mapping`, `Precoding`, and `Layer Recovery / De-precoding`.

**Recommended setup**

- layer count: `1`, then `2`, then `4` if feasible
- same channel and SNR
- compare different precoders or codebooks

**Artifacts to emphasize**

- symbols per layer
- precoder matrix
- post-de-precoding constellation per layer
- layer-wise KPI placeholders

**Expected conclusion**

Spatial multiplexing can increase throughput, but only when the channel and recovery processing are good enough to separate layers reliably.

### UC-12: Decoder-Input Quality Study

**Goal**

Explain decoder behavior in terms of soft information, not only hard BER.

**Recommended setup**

- keep modulation fixed
- vary SNR, CE quality, and equalizer settings
- inspect the same scenario under multiple impairment settings

**Artifacts to emphasize**

- LLR histogram
- mean absolute LLR
- sign distribution
- optional saturation/clipping indicators

**Expected conclusion**

The decoder does not only care about whether symbols look approximately correct. It cares about the confidence structure represented in the LLRs.

## Recommended Priorities

If the full-option pipeline is implemented incrementally, the highest-value order is:

1. `Remove CP`
2. `Resource Element Extraction`
3. `Descrambling` as an explicit GUI block
4. `Rate Recovery`
5. `Soft LLR Buffer`
6. `Layer Mapping`
7. `Precoding`
8. `Layer Recovery / De-precoding`
9. `RF front-end TX/RX models`

## Reporting Template

For each use case, the recommended report structure is:

1. `Objective`
2. `Scenario and PHY configuration`
3. `Channel and impairment settings`
4. `Receiver assumptions`
5. `Artifacts inspected`
6. `KPI summary`
7. `Interpretation`
8. `Limitations / placeholders`

## Placeholder Sections

The following placeholders are intentionally left for later expansion when the corresponding blocks are implemented:

- `Placeholder: layer-wise KPI table for multi-layer MIMO`
- `Placeholder: precoder codebook comparison figures`
- `Placeholder: RF front-end nonlinearity model equations`
- `Placeholder: measured runtime vs capture_slots scaling table`
