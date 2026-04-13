# Teaching Labs 6 Session Series for 5G NR PHY STL

## Purpose

Tai lieu nay bien repo hien tai thanh mot chuoi `6 bai lab` co the day that trong hoc phan `5G physical layer`.

Moi bai lab duoc thiet ke theo logic:

- co muc tieu hoc tap ro
- co lenh chay cu the
- co cau hinh GUI / CLI cu the
- co ket qua mong doi
- co cau hoi thao luan

## Common Setup

Thu muc goc:

```powershell
cd D:\Data\Lectures\20252\MobiCom\Codex\5GNRPHYSITL\5gnr_phy_stl
```

GUI khuyen nghi:

```powershell
C:\Users\tuan.dotrong\AppData\Local\radioconda\python.exe main.py --config configs/default.yaml --gui
```

Neu khong can GNU Radio:

```powershell
.\.venv\Scripts\python.exe main.py --config configs/default.yaml --gui
```

## Lab 1. End-to-End Downlink PHY

### Objective

- Hieu chuoi PHY downlink co ban
- Xac dinh block nao lam gi trong TX, channel, RX

### Run

```powershell
python main.py --config configs/default.yaml --gui
```

### GUI settings

- `Mode = data`
- `Direction = downlink`
- `Modulation = QPSK`
- `Channel model = awgn`
- `SNR = 20 dB`
- `Capture slots = 1`
- `Perfect sync = On`
- `Perfect CE = On`

### Student tasks

1. Bam `Step Mode`
2. Liet ke ten cac block trong `PHY Pipeline`
3. Ghi chu domain cua 5 stage:
   - `Bits`
   - `Modulation mapping`
   - `Resource Grid + RS`
   - `OFDM / IFFT + CP`
   - `Soft LLR before decoding`

### Expected observations

- `BER = 0`
- `BLER = 0`
- constellation sau EQ sach
- CRC pass

### Deliverable

- bang 2 cot:
  - `Stage`
  - `Input / Output domain`

## Lab 2. Resource Grid and Reference Signals

### Objective

- Phan biet `PDSCH`, `PDCCH/CORESET`, `PBCH/SSB`
- Quan sat `DMRS`, `CSI-RS`, `SRS`, `PT-RS`

### Runs

Downlink control:

```powershell
python main.py --config configs/default.yaml --channel-type control --gui
```

PBCH:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_pbch_baseline.yaml --gui
```

Uplink data:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_uplink_baseline.yaml --gui
```

### Student tasks

1. So sanh allocation map cua:
   - `data`
   - `control`
   - `pbch`
2. Xac dinh:
   - RE nao la payload
   - RE nao la pilot/reference
3. Giai thich vi sao `SRS` khong xuat hien trong downlink run

### Expected observations

- control co `CORESET / SearchSpace`
- PBCH co `SSB / PBCH Broadcast Layout`
- uplink data co `SRS`
- downlink data/control co `CSI-RS`
- scheduled data co `PT-RS`

### Deliverable

- 3 hinh chup allocation map
- 1 bang tong hop reference signals theo tung mode

## Lab 3. Uplink, PRACH, and Broadcast Roles

### Objective

- Phan biet:
  - `PUSCH-style`
  - `PUCCH-style`
  - `PRACH`
  - `PBCH`

### Runs

Uplink data:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_uplink_baseline.yaml --gui
```

Uplink control:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_uplink_control_baseline.yaml --gui
```

PRACH:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_uplink_prach_baseline.yaml --gui
```

PBCH:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_pbch_baseline.yaml --gui
```

### Student tasks

1. Tim 2 block co trong PRACH ma khong co trong PUSCH
2. Tim 2 diem khac nhau giua PBCH va PDSCH
3. Giai thich tai sao PRACH la `detection problem`, khong phai `file/data transport problem`

### Expected observations

- PRACH co `correlation detector`
- uplink data co `transform precoding` option
- uplink control co payload ngan hon va path control rieng
- PBCH nam trong `SSB`

### Deliverable

- 1 slide so sanh `PUSCH / PUCCH / PRACH / PBCH`

## Lab 4. Receiver Realism and Channel Impairments

### Objective

- Hieu tac dong cua:
  - `Perfect sync`
  - `Perfect CE`
  - `CFO`
  - `STO`
  - `phase noise`
  - `vehicular fading`

### Runs

GUI default:

```powershell
python main.py --config configs/default.yaml --gui
```

GUI vehicular:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_vehicular.yaml --gui
```

Batch impairment:

```powershell
python run_experiments.py --experiment impairment_sweep --config configs/default.yaml --output-dir outputs
```

### Student tasks

1. Chay voi `Perfect sync = On`, `Perfect CE = On`
2. Lap lai voi ca hai `Off`
3. Tang `CFO`
4. Tang `STO`
5. Chuyen sang `vehicular`
6. Ghi lai block nao bat dau xuong cap truoc

### Expected observations

- timing metric va CFO trace xau di truoc khi CRC fail
- channel estimate xau lam constellation sau EQ mo rong
- `LLR` histogram kem chac chan hon

### Deliverable

- bang 3 cot:
  - `Condition`
  - `First artifact that degrades`
  - `Final KPI impact`

## Lab 5. File Transfer over PHY

### Objective

- Noi `PHY reliability` voi `application outcome`
- So sanh file text nho va file anh lon

### Runs

Text:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_text_transfer.yaml --gui
```

Image:

```powershell
python main.py --config configs/default.yaml --override configs/scenario_image_transfer.yaml --gui
```

CLI alternative:

```powershell
python main.py --config configs/default.yaml --tx-file input/sample_message.txt --rx-output-dir outputs/rx_files
python main.py --config configs/default.yaml --tx-file input/sample_image.png --rx-output-dir outputs/rx_files
```

### Student tasks

1. Chay text o `SNR = 40 dB`
2. Chay image o `SNR = 40 dB`
3. Giam `SNR`
4. Tat `Perfect sync` va `Perfect CE`
5. Ghi lai:
   - so chunk
   - co ghi file RX hay khong
   - `chunks_failed`

### Expected observations

- text de pass hon image
- file lon nhay hon vi co nhieu chunk
- chi can 1 chunk fail CRC la file khong duoc phuc hoi

### Deliverable

- bang:
  - `File type`
  - `SNR`
  - `Success`
  - `chunks_failed`

## Lab 6. Batch Analytics and Mini Report

### Objective

- Day sinh vien cach thu nghiem co he thong
- Day cach doc file CSV/plot va viet ket luan

### Runs

File-transfer sweep:

```powershell
python run_experiments.py --experiment sample_file_transfer_sweep --config configs/default.yaml --override configs/scenario_sample_file_transfer_sweep.yaml --output-dir outputs
```

BER sweep:

```powershell
python run_experiments.py --experiment ber_vs_snr --config configs/default.yaml --output-dir outputs
```

BLER sweep:

```powershell
python run_experiments.py --experiment bler_vs_snr --config configs/default.yaml --output-dir outputs
```

### Student tasks

1. Mo file:
   - `outputs/sample_inputs/file_transfer_sweep/file_transfer_sweep.csv`
   - `outputs/sample_inputs/file_transfer_sweep/file_transfer_success_vs_snr.png`
   - `outputs/sample_inputs/file_transfer_sweep/file_transfer_chunks_failed_vs_snr.png`
2. Chon 1 trong 2 bai:
   - `BER vs SNR`
   - `File success vs SNR`
3. Viet mini report `2 trang`

### Required report sections

- `Scenario`
- `Configuration`
- `Observed artifacts`
- `Main KPI results`
- `Interpretation`
- `Limitations of the simulator`

### Expected outcome

- sinh vien khong chi nhin GUI
- sinh vien co the doc du lieu batch va viet ket luan ky thuat

## Suggested Semester Order

| Week | Lab | Theme |
| --- | --- | --- |
| `1` | `Lab 1` | End-to-end PHY chain |
| `2` | `Lab 2` | Grid and reference signals |
| `3` | `Lab 3` | DL vs UL vs RA vs broadcast |
| `4` | `Lab 4` | Impairments and realistic receiver |
| `5` | `Lab 5` | PHY impact on applications |
| `6` | `Lab 6` | Batch analytics and reporting |

## What Students Should Not Overclaim

Can yeu cau sinh vien ghi ro:

- project nay chua co `MIMO`
- chua co `HARQ`
- chua co `CQI / PMI / RI`
- chua co `scheduler / DCI` day du
- `PBCH`, `CSI-RS`, `SRS`, `PT-RS`, `CORESET / SearchSpace` moi la baseline

Neu sinh vien viet report, nen co mot muc:

- `Simulator assumptions and realism limits`

## Placeholder Additions

- Placeholder: mau template report 2 trang
- Placeholder: bo screenshot chuan cho 6 bai lab
- Placeholder: rubric cham diem
- Placeholder: dap an mau cho tung lab
