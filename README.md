# BIM 效益衡量系統

這是把原本 WinForms/C# 專案中「資料結構 + 平均/標準差 + 正規化 + 類 RBF 加權推估」轉成 Python 3.12 的可執行版本。

> 原本 C# 版用 Microsoft Solver Foundation 去「學習權重」。  
> Python 版目前先給 **可跑的預設權重（全部 1.0）**，並保留可擴充點：後續可以加上學習/最佳化。

---

## 1) 在 PyCharm 跑起來

1. 確認 Python 為 3.12（3.11 亦可）。
2. 安裝唯一的 Excel 讀取依賴：
   ```bash
   python -m pip install -r requirements.txt
   ```
3. 執行：
   ```bash
   python main.py
   ```

程式會自動載入 `dataset/完整案例庫_新增BIM標註.xls`。此資料集的預算、決標金額、工期與結算金額完整的案例會轉成訓練資料；工期由實際開工／完工日計算。

---

## 2) 訓練資料格式（CSV 或 XLS）

你可以用「資料管理」分頁載入 `.csv` 或附帶的舊版 Excel `.xls`。CSV 第一列須有下列 header：

- id
- name
- procurement_raw
- tender_value_raw
- floor_raw
- basement_raw
- floor_area_raw
- pre_duration_raw
- duration_actual
- settlement_raw

---

## 3) 訓練權重（取代 Solver Foundation）

在專案資料夾內執行：

```bash
python train_weights.py --target duration --iters 6000 --seed 42
python train_weights.py --target settlement --iters 6000 --seed 42
```

會在專案資料夾產生 `weights.json`。duration 與 settlement 權重會分開儲存，GUI 會將各自的權重套用到對應推估頁面。


## 4) GUI 重新載入權重

- 訓練完 `train_weights.py` 會產生 `weights.json`
- GUI 的「資料管理」分頁有 **Reload Weights** 按鈕
