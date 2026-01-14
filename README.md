# BIM效益衡量系統（Python 3.12 可跑版）

這是把原本 WinForms/C# 專案中「資料結構 + 平均/標準差 + 正規化 + 類RBF加權推估」先轉成 **純 Python 3.12（無額外依賴）** 能跑的版本。

> 原本 C# 版用 Microsoft Solver Foundation 去「學習權重」。  
> Python 版目前先給 **可跑的預設權重（全部 1.0）**，並保留可擴充點：後續可以加上學習/最佳化。

---

## 1) 在 PyCharm 跑起來

1. 把整個資料夾 `bim_benefit_app_py` 用 PyCharm 開起來  
2. 確認 Interpreter 是 Python 3.12  
3. 執行 `main.py`

---

## 2) 訓練資料格式（CSV）

你可以用「資料」分頁載入 CSV。欄位如下（第一列要有 header）：

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

## 2) 訓練權重（取代 Solver Foundation）

在專案資料夾內執行：

```bash
python train_weights.py --target duration --iters 6000 --seed 42
python train_weights.py --target settlement --iters 6000 --seed 42
```

會在專案資料夾產生 `weights.json`。GUI 啟動時若偵測到 `weights.json`，推估會自動套用訓練後的權重。


## 3) GUI 重新載入權重

- 訓練完 `train_weights.py` 會產生 `weights.json`
- GUI 右上角（資料分頁）有 **Reload weights.json** 按鈕
- 推估分頁會以 2x3 卡片顯示目前權重（含 ⭐ Top / 🔥/❄️）
