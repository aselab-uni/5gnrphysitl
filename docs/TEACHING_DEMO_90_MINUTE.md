# Teaching Demo 90 Minutes for 5G NR PHY STL

## Scope

Tai lieu nay la giao an demo `90 phut` de day hoc bang chinh codebase hien tai.

Muc tieu:

- gioi thieu cho sinh vien chuoi xu ly PHY cua 5G NR o muc link-level
- cho sinh vien thay duoc su khac nhau giua `data`, `control`, `uplink`, `PRACH`, `PBCH`
- lien he giua artifact trong GUI va KPI cuoi cung
- ket noi `PHY behavior` voi `application outcome` thong qua file transfer

Tai lieu nay bam theo dung kha nang hien co cua repo, khong gia dinh da co MIMO, HARQ, CQI/PMI/RI, hay scheduler day du.

## Audience

Phu hop cho:

- sinh vien nam 3, nam 4 cac nganh vien thong / dien tu / mang
- hoc vien cao hoc can mot cong cu truc quan de hieu link-level PHY
- giang vien muon demo 5G PHY ma khong can SDR that

## Prerequisites

- Project root:
  - `D:\Data\Lectures\20252\MobiCom\Codex\5GNRPHYSITL\5gnr_phy_stl`
- Moi truong:
  - Windows PowerShell
  - Radioconda hoac `.venv`
- Neu muon co `TX sink` / `RX sink`, chay bang Radioconda

Lenh mo GUI khuyen nghi:

```powershell
cd D:\Data\Lectures\20252\MobiCom\Codex\5GNRPHYSITL\5gnr_phy_stl
C:\Users\tuan.dotrong\AppData\Local\radioconda\python.exe main.py --config configs/default.yaml --gui
```

## Learning Outcomes

Sau buoi demo, sinh vien nen:

- mo ta duoc chuoi `Bits -> CRC -> Coding -> Rate Matching -> Scrambling -> QAM -> Grid -> OFDM -> Channel -> RX`
- phan biet `downlink`, `uplink`, `random access`, `broadcast`
- doc duoc `resource grid`, `reference signals`, `constellation`, `LLR`, `BER/BLER/EVM`
- giai thich duoc vi sao `Perfect sync` / `Perfect CE` lam nguong loi dep hon
- lien he duoc su suy giam PHY voi viec pass/fail khi truyen file text/anh

## Demo Structure

| Segment | Time | Main topic | Goal |
| --- | --- | --- | --- |
| `S1` | `0-10 min` | Setup + architecture orientation | Dat bo canh dung cho repo |
| `S2` | `10-25 min` | End-to-end PHY chain | Hieu toan chuoi TX -> Channel -> RX |
| `S3` | `25-40 min` | Resource grid, CORESET, SSB, reference signals | Hieu resource elements va pilot |
| `S4` | `40-55 min` | Uplink, PRACH, PBCH | Hieu phan biet giua DL, UL, RA, broadcast |
| `S5` | `55-75 min` | Imperfections and realistic receiver | Thay vi sao sync/CE la khoa |
| `S6` | `75-90 min` | File transfer + batch analytics | Noi PHY voi outcome thuc te |

## Segment S1. Setup and Orientation (0-10 min)

### What to show

- Cau truc project
- Vai tro cua GUI
- Y nghia cua `Run`, `Step Mode`, `Capture slots`

### Files to reference

- [README.md](/D:/Data/Lectures/20252/MobiCom/Codex/5GNRPHYSITL/5gnr_phy_stl/README.md)
- [TECHDOC_5G_NR_PHY_TRACE.md](/D:/Data/Lectures/20252/MobiCom/Codex/5GNRPHYSITL/5gnr_phy_stl/docs/TECHDOC_5G_NR_PHY_TRACE.md)

### Talk track

- Repo nay la `software-only, link-level, visually inspectable NR PHY simulator`
- No rat hop de day `PHY chain`, khong phai de day `full 5G system stack`
- Diem manh lon nhat la `PHY Pipeline`

### Instructor action

Mo GUI:

```powershell
C:\Users\tuan.dotrong\AppData\Local\radioconda\python.exe main.py --config configs/default.yaml --gui
```

Chi nhanh:

- panel trai: tham so
- o giua: tabs
- panel phai: KPI + log + environment status

## Segment S2. End-to-End PHY Walkthrough (10-25 min)

### Scenario

Baseline downlink data.

### GUI settings

- `Mode = data`
- `Direction = downlink`
- `Modulation = QPSK`
- `Channel model = awgn`
- `SNR = 20 dB`
- `Capture slots = 1`
- `Perfect sync = On`
- `Perfect CE = On`

### Instructor action

1. Bam `Step Mode`
2. Vao tab `PHY Pipeline`
3. Di qua tung block:
   - `Traffic / transport block`
   - `TB CRC attachment`
   - `Code block segmentation + CB CRC`
   - `Channel coding`
   - `Rate matching`
   - `Scrambling`
   - `Modulation mapping`
   - `Resource Grid + RS`
   - `OFDM / IFFT + CP`
   - `RF/baseband impairments`
   - `Timing / CFO correction`
   - `Remove CP`
   - `FFT`
   - `Resource element extraction`
   - `Channel estimation`
   - `Equalization`
   - `Soft demapping`
   - `Rate recovery`
   - `Soft LLR before decoding`
   - `Decoding`
   - `CRC check`

### Questions to ask students

- Block nao chuyen tu `bits` sang `symbols`?
- Block nao chuyen tu `grid` sang `waveform`?
- Tai sao decoder can `LLR` thay vi chi hard bits?

### Expected outcome

- constellation sach
- `BER = 0`
- `BLER = 0`
- sinh vien nam duoc chuoi end-to-end

## Segment S3. Resource Grid, CORESET, SSB, and Reference Signals (25-40 min)

### Goal

Cho sinh vien thay su khac nhau giua:

- `PDSCH-style`
- `PDCCH/CORESET-style`
- `SSB/PBCH-style`
- `DMRS`, `CSI-RS`, `SRS`, `PT-RS`

### Part A. Downlink control

Run:

```powershell
python main.py --config configs/default.yaml --channel-type control --gui
```

Hoac:

```powershell
python main.py --config configs/default.yaml --gui
```

roi dat:

- `Mode = control`
- `Direction = downlink`

### What to highlight

- `CORESET / SearchSpace selection` stage
- allocation map trong `Resource Grid`
- vi sao control khong map giong data

### Part B. PBCH / SSB

Run:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_pbch_baseline.yaml --gui
```

### What to highlight

- `SSB / PBCH Broadcast Layout`
- vung `SSB`
- `PSS`, `SSS`, `PBCH-DMRS`
- PBCH payload chi nam trong mot phan cua broadcast region

### Reference-signal discussion

Chi cho sinh vien:

- `DMRS` dung cho estimation chinh
- `CSI-RS` dung cho sounding / future CSI logic
- `SRS` chi co tren uplink
- `PT-RS` dung de pha-tracking quan sat duoc, chua phai full 3GPP procedure

## Segment S4. Uplink, PRACH, and PBCH Roles (40-55 min)

### Part A. Uplink data

Run:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_uplink_baseline.yaml --gui
```

Highlight:

- `Direction = uplink`
- `PUSCH-style`
- `Transform precoding` toggle

Neu muon doi sang DFT-s-OFDM style:

- tick `Transform precoding`
- bam `Run`

### Part B. Uplink control

Run:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_uplink_control_baseline.yaml --gui
```

Highlight:

- control payload ngan
- `PUCCH-style`
- control coder khac data coder

### Part C. PRACH

Run:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_uplink_prach_baseline.yaml --gui
```

Highlight:

- PRACH khong phai data link
- `PRACH preamble generation`
- `PRACH correlation detector`
- `PRACH decision`

### Questions to ask students

- PRACH khac PUSCH o diem nao?
- Tai sao PBCH la broadcast path, con PRACH la access path?

## Segment S5. Imperfections and Realistic Receiver (55-75 min)

### Goal

Cho sinh vien thay:

- receiver ly tuong va receiver thuc te khac nhau the nao
- impairment xuat hien som nhat o artifact nao

### GUI settings

Ban 1:

- `Perfect sync = On`
- `Perfect CE = On`

Ban 2:

- `Perfect sync = Off`
- `Perfect CE = Off`

Sau do thay doi:

- `CFO`
- `STO`
- `Phase noise`
- `SNR`

### Suggested run order

1. `SNR = 20 dB`, perfect on
2. `SNR = 20 dB`, perfect off
3. tang `CFO`
4. tang `STO`
5. chuyen sang `vehicular`

Lenh scenario vehicular:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_vehicular.yaml --gui
```

### What to show

- `Timing / CFO correction`
- `Remove CP`
- `FFT`
- `Channel estimation`
- `Equalization`
- `Soft LLR before decoding`
- KPI: `BER`, `BLER`, `EVM`, `estimated_snr_db`

### Teaching message

- loi he thong khong nhat thiet bat dau o decoder
- nhieu khi no bat dau tu sync hoac CE, sau do moi lan toi `LLR` va `CRC`

## Segment S6. File Transfer and Batch Analytics (75-90 min)

### Part A. Text and image transfer

Run:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_text_transfer.yaml --gui
python main.py --config configs/default.yaml --override configs/scenario_image_transfer.yaml --gui
```

### What to show

- `File Source + Packaging`
- `File Reassembly + Write`
- ten file RX co `snr` + `timestamp`
- file text thuong de pass hon file anh

### Main teaching point

Application-level result la `all-or-nothing`:

- tat ca chunks pass -> file RX byte-perfect
- chi can 1 chunk fail -> file khong duoc ghi

### Part B. Batch sweep

Run:

```powershell
python run_experiments.py --experiment sample_file_transfer_sweep --config configs/default.yaml --override configs/scenario_sample_file_transfer_sweep.yaml --output-dir outputs
```

Open and discuss:

- `outputs/sample_inputs/file_transfer_sweep/file_transfer_sweep.csv`
- `outputs/sample_inputs/file_transfer_sweep/file_transfer_success_vs_snr.png`
- `outputs/sample_inputs/file_transfer_sweep/file_transfer_chunks_failed_vs_snr.png`

### Wrap-up message

- cung mot PHY chain
- text va image co behavior khac nhau do `chunk count`
- day la cau noi rat tot tu `PHY KPI` sang `user-perceived outcome`

## Teaching Risks and How to Frame Them

Can noi ro voi sinh vien:

- repo nay **khong co MIMO**
- repo nay **khong co HARQ soft combining**
- `CSI-RS`, `SRS`, `PT-RS`, `PBCH`, `CORESET` moi la baseline
- day la `teaching / research simulator`, khong phai `conformance-grade NR stack`

Neu noi ro nhu vay, repo se rat manh cho day hoc thay vi gay hieu nham.

## Minimal Demo Checklist

Truoc gio day, chay truoc:

```powershell
python -m pytest -q
python main.py --config configs/default.yaml
python main.py --config configs/default.yaml --override configs/scenario_pbch_baseline.yaml
python main.py --config configs/default.yaml --override configs/scenario_uplink_prach_baseline.yaml
```

Trong lop, can mo san:

- GUI default
- GUI PBCH
- GUI PRACH
- file text/image sample
- batch output folder

## Placeholder Figures

- Placeholder: screenshot `PHY Pipeline` o baseline downlink data
- Placeholder: screenshot `CORESET / SearchSpace Selection`
- Placeholder: screenshot `SSB / PBCH Broadcast Layout`
- Placeholder: screenshot `PRACH correlation detector`
- Placeholder: screenshot `File Reassembly + Write`
