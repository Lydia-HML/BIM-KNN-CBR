# BIM Benefit Evaluation System / BIM 效益衡量系統

This is an executable Python port of the original WinForms/C# project. It provides data structures, mean and standard-deviation normalization, and RBF-style weighted predictions.

這是原 WinForms/C# 專案的可執行 Python 版本，提供資料結構、平均值與標準差正規化，以及類 RBF 加權推估。

> The original C# application learned weights with Microsoft Solver Foundation. This Python implementation starts with runnable default weights (all `1.0`) and includes a training script for further optimization.
>
> 原 C# 版使用 Microsoft Solver Foundation 學習權重。Python 版本預設使用可執行的權重（皆為 `1.0`），並提供訓練腳本以進一步最佳化。

---

## 1. Run the application / 執行程式

1. Use Python 3.12; Python 3.11 is also supported.
2. Install the Excel-reading dependency:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Start the GUI:

   ```bash
   python main.py
   ```

1. 使用 Python 3.12；Python 3.11 亦支援。
2. 安裝 Excel 讀取依賴：

   ```bash
   python -m pip install -r requirements.txt
   ```

3. 啟動 GUI：

   ```bash
   python main.py
   ```

The application automatically loads `dataset/完整案例庫_新增BIM標註.xls`. Records with complete budget, tender value, actual duration, and settlement data are converted into training projects. Actual duration is calculated from the actual start and completion dates.

程式會自動載入 `dataset/完整案例庫_新增BIM標註.xls`。具備完整預算、決標金額、實際工期與結算金額的案例會轉成訓練資料；實際工期由實際開工日與完工日計算。

---

## 2. Training data format / 訓練資料格式

Use the **Data Management / 資料管理** tab to load a `.csv` file or the bundled legacy Excel `.xls` dataset. A CSV file must include this header row:

可使用「**資料管理 / Data Management**」分頁載入 `.csv`，或使用附帶的舊版 Excel `.xls` 資料集。CSV 第一列必須包含下列欄位：

```text
id,name,procurement_raw,tender_value_raw,floor_raw,basement_raw,floor_area_raw,pre_duration_raw,duration_actual,settlement_raw
```

| Column / 欄位 | Description / 說明 |
|---|---|
| `id` | Project identifier / 案例識別碼 |
| `name` | Project name / 案例名稱 |
| `procurement_raw` | Procurement budget / 發包預算 |
| `tender_value_raw` | Tender value / 決標金額 |
| `floor_raw` | Above-ground floor count / 地上層數 |
| `basement_raw` | Basement floor count / 地下層數 |
| `floor_area_raw` | Total floor area / 總樓地板面積 |
| `pre_duration_raw` | Planned duration in days / 預定總天數 |
| `duration_actual` | Actual duration in days / 實際總天數 |
| `settlement_raw` | Settlement amount / 結算金額 |

---

## 3. Train weights / 訓練權重

Run the following commands from the project directory:

在專案根目錄執行：

```bash
python train_weights.py --target duration --iters 6000 --seed 42
python train_weights.py --target settlement --iters 6000 --seed 42
```

The commands create `weights.json`. Duration and settlement weights are stored independently, and the GUI applies each weight set to its matching prediction page.

指令會建立 `weights.json`。duration 與 settlement 權重會分開儲存，GUI 會在對應的推估頁面套用各自的權重。

To train on another CSV or XLS file, pass `--data`:

若要使用其他 CSV 或 XLS 檔案訓練，請指定 `--data`：

```bash
python train_weights.py --data path/to/cases.csv --target duration --iters 6000 --seed 42
```

---

## 4. Reload weights in the GUI / 在 GUI 重新載入權重

After training, select **Reload Weights** in the **Data Management / 資料管理** tab. The application reports how many target-specific weight sets were loaded.

完成訓練後，請在「**資料管理 / Data Management**」分頁按下 **Reload Weights**。程式會顯示成功載入的目標權重組數。

---

## 5. Verify the data pipeline / 驗證資料流程

Run the bundled test to verify that the included XLS dataset can be loaded and used for prediction:

執行內附測試，確認附帶的 XLS 資料集能被讀取並用於推估：

```bash
python -m unittest discover -s tests -v
```
