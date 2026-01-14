from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from models import Project
from system_stats import MySystem
from io_csv import load_projects_csv, save_projects_csv
from rbf_predictor import rbf_predict, RBFWeights


class App(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.master.title("BIM 效益評估決策支持系統")
        self.master.geometry("900x850")  # Increased height to prevent UI cutoff
        self.pack(fill="both", expand=True)

        self.base_dir = Path(__file__).parent
        self.system = MySystem()
        self.weights: RBFWeights | None = None

        # Stored results for comparison
        self.res_cost = 0.0
        self.res_sched = 0.0

        self._build_ui()
        self._autoload_data()
        self._autoload_weights()

    def _build_ui(self) -> None:
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        # Create 4 main tabs
        self.tab_data = ttk.Frame(self.nb)
        self.tab_cost = ttk.Frame(self.nb)
        self.tab_sched = ttk.Frame(self.nb)
        self.tab_compare = ttk.Frame(self.nb)

        self.nb.add(self.tab_data, text=" (1) 資料管理 ")
        self.nb.add(self.tab_cost, text=" (2) Cost 估算 ")
        self.nb.add(self.tab_sched, text=" (3) Schedule 估算 ")
        self.nb.add(self.tab_compare, text=" (4) 結果比較 ")

        self._setup_data_tab()
        # Setup specific tabs for Cost and Schedule
        self._setup_predict_tab(self.tab_cost, "Cost (Settlement)", lambda p: p.settlement_raw)
        self._setup_predict_tab(self.tab_sched, "Schedule (Duration)", lambda p: p.duration_actual)
        self._setup_compare_tab()

    def _setup_data_tab(self) -> None:
        row = 0
        ttk.Button(self.tab_data, text="載入 CSV 訓練案例", command=self.load_csv).grid(row=row, column=0, padx=5,
                                                                                        pady=5)
        ttk.Button(self.tab_data, text="匯出資料 CSV", command=self.export_csv).grid(row=row, column=1, padx=5, pady=5)
        ttk.Button(self.tab_data, text="Reload Weights", command=self.reload_weights).grid(row=row, column=2, padx=5,
                                                                                           pady=5)

        row += 1
        self.lbl_stats = ttk.Label(self.tab_data, text="尚未載入資料。")
        self.lbl_stats.grid(row=row, column=0, columnspan=3, sticky="w", padx=5, pady=10)

        row += 1
        self.lbl_status = ttk.Label(self.tab_data, text="", foreground="gray")
        self.lbl_status.grid(row=row, column=0, columnspan=3, sticky="w", padx=5)

    def _setup_predict_tab(self, tab, title, y_getter):
        """Standardized layout for prediction tabs."""
        # Shared input frame
        frm = ttk.LabelFrame(tab, text=f"輸入測試案例特徵 - {title}")
        frm.pack(fill="x", padx=10, pady=5)

        inputs = {}
        fields = [
            ("發包預算 (Procurement)", "procurement_raw"),
            ("決標金額 (Tender Value)", "tender_value_raw"),
            ("地上層數 (Floor)", "floor_raw"),
            ("地下層數 (Basement)", "basement_raw"),
            ("總樓地板面積 (Area)", "floor_area_raw"),
            ("預定總天數 (Pre-Duration)", "pre_duration_raw"),
        ]

        for i, (label, key) in enumerate(fields):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky="w", padx=6, pady=2)
            e = ttk.Entry(frm, width=25)
            e.grid(row=i, column=1, sticky="w", padx=6, pady=2)
            e.insert(0, "0")
            inputs[key] = e

        # Add RBF Param
        prm = ttk.Frame(tab)
        prm.pack(fill="x", padx=10)
        ttk.Label(prm, text="Radius (rad):").pack(side="left", padx=5)
        ent_rad = ttk.Entry(prm, width=10)
        ent_rad.pack(side="left", padx=5)
        ent_rad.insert(0, "1.0")

        # Estimation Button
        btn = ttk.Button(tab, text=f"執行 {title} 核心推估",
                         command=lambda: self._run_prediction(title, y_getter, inputs, ent_rad, tab))
        btn.pack(pady=10)

        # Output Text
        txt = tk.Text(tab, height=10, font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=10, pady=5)

        # Store references in the tab object
        tab.inputs = inputs
        tab.ent_rad = ent_rad
        tab.output_text = txt

    def _setup_compare_tab(self):
        frm = ttk.Frame(self.tab_compare, padding=30)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="BIM 效益推估整合報告", font=("Arial", 18, "bold")).pack(pady=20)

        self.lbl_cost_res = ttk.Label(frm, text="Cost 預測結果：尚未計算", font=("Arial", 13))
        self.lbl_cost_res.pack(pady=10, anchor="w")

        self.lbl_sched_res = ttk.Label(frm, text="Schedule 預測結果：尚未計算", font=("Arial", 13))
        self.lbl_sched_res.pack(pady=10, anchor="w")

        ttk.Button(frm, text="更新比較數據", command=self._refresh_comparison).pack(pady=30)

    def _run_prediction(self, mode, y_getter, inputs, ent_rad, tab):
        if not self.system.projects:
            messagebox.showwarning("錯誤", "請先載入訓練資料。")
            return

        try:
            rad = float(ent_rad.get().strip())
        except:
            rad = 1.0

        test = Project(
            id=0, name="test",
            procurement_raw=float(inputs["procurement_raw"].get() or 0),
            tender_value_raw=float(inputs["tender_value_raw"].get() or 0),
            floor_raw=float(inputs["floor_raw"].get() or 0),
            basement_raw=float(inputs["basement_raw"].get() or 0),
            floor_area_raw=float(inputs["floor_area_raw"].get() or 0),
            pre_duration_raw=float(inputs["pre_duration_raw"].get() or 0),
        )
        test.system = self.system

        y_hat, top_cases = rbf_predict(test, self.system.projects, y_getter, rad=rad, weights=self.weights)

        if "Cost" in mode:
            self.res_cost = y_hat
        else:
            self.res_sched = y_hat

        tab.output_text.delete("1.0", "end")
        tab.output_text.insert("end", f"== {mode} 推估結果 ==\n")
        tab.output_text.insert("end", f"預測數值: {y_hat:.4f}\n\n")
        tab.output_text.insert("end", "最相近訓練案例 (Top 10):\n")

        for i, (pid, w) in enumerate(top_cases[:10], 1):
            tab.output_text.insert("end", f"{i:02d}. [ID: {pid}] 相似度權重: {w:.4f}\n")

        messagebox.showinfo("完成", f"{mode} 推估計算成功！")

    def _refresh_comparison(self):
        self.lbl_cost_res.config(text=f"Cost 預測結果 (結算金額)：$ {self.res_cost:,.2f}")
        self.lbl_sched_res.config(text=f"Schedule 預測結果 (總天數)：{self.res_sched:.2f} 天")

    # --- Autoload and Helper methods (Same as original) ---
    def _autoload_data(self):
        csv_path = self.base_dir / "data.csv"
        if csv_path.exists():
            try:
                self.system.projects = load_projects_csv(csv_path)
                self.system.attach()
                self._refresh_stats()
                self._set_status(f"自動載入 data.csv 成功 ({len(self.system.projects)} 筆)")
            except Exception as e:
                self._set_status(f"載入失敗: {e}")

    def _autoload_weights(self):
        wpath = self.base_dir / "weights.json"
        if wpath.exists():
            try:
                with wpath.open("r", encoding="utf-8") as f:
                    w = json.load(f).get("weights", {})
                self.weights = RBFWeights(**{k: float(v) for k, v in w.items()})
            except:
                self.weights = None

    def _set_status(self, msg):
        self.lbl_status.config(text=msg)

    def _refresh_stats(self):
        n = len(self.system.projects)
        self.lbl_stats.config(text=f"已載入 {n} 筆案例資料。")

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            self.system.projects = load_projects_csv(path)
            self.system.attach()
            self._refresh_stats()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path: save_projects_csv(path, self.system.projects)

    def reload_weights(self):
        self._autoload_weights()
        messagebox.showinfo("OK", "權重已更新。")


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

