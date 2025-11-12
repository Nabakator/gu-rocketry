#!/usr/bin/env python3
"""
Parachute Design Helping Tool — QtPy GUI

Implements a simple cross-binding Qt GUI (QtPy) for single or dual deployment sizing.

Equations (for round canopies):
    • S = (2 g m) / (rho C_d V^2)
    • D = sqrt(4 S / π)

Dual deployment:
    • Uses an average C_d = (C_d_drogue + C_d_main)/2 for total sizing.
    • Splits total area by a user-selectable drogue fraction (default 20%).

Rounding:
    • Optional rounding of diameters to whole feet (nearest / up / down) for purchase sizing.
    • If < 1 ft, the GUI also provides inch equivalents (rounded to the nearest inch).

Dependencies:
    pip install qtpy PyQt5 numpy   # (or PySide6 instead of PyQt5)

Run:
    python parachute_gui.py
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import numpy as np
from qtpy import QtCore, QtGui, QtWidgets

# -----------------------------
# Physical & unit conversions
# -----------------------------
M2_TO_FT2 = 10.7639     # 1 m^2 = 10.7639 ft^2
M_TO_IN   = 39.3701     # 1 m = 39.3701 in
M_TO_FT   = 3.28084     # 1 m = 3.28084 ft
PI        = math.pi


@dataclass
class SingleResult:
    S_total_m2: float
    D_total_m: float

    @property
    def S_total_ft2(self) -> float:
        return self.S_total_m2 * M2_TO_FT2

    @property
    def D_total_in(self) -> float:
        return self.D_total_m * M_TO_IN

    @property
    def D_total_ft(self) -> float:
        return self.D_total_m * M_TO_FT


@dataclass
class DualResult:
    # Totals
    S_total_m2: float
    D_total_m: float
    # Drogue
    S_drogue_m2: float
    D_drogue_m: float
    # Main
    S_main_m2: float
    D_main_m: float

    # Convenience properties
    @property
    def S_total_ft2(self) -> float:
        return self.S_total_m2 * M2_TO_FT2

    @property
    def D_total_ft(self) -> float:
        return self.D_total_m * M_TO_FT

    @property
    def D_total_in(self) -> float:
        return self.D_total_m * M_TO_IN

    @property
    def S_drogue_ft2(self) -> float:
        return self.S_drogue_m2 * M2_TO_FT2

    @property
    def D_drogue_ft(self) -> float:
        return self.D_drogue_m * M_TO_FT

    @property
    def D_drogue_in(self) -> float:
        return self.D_drogue_m * M_TO_IN

    @property
    def S_main_ft2(self) -> float:
        return self.S_main_m2 * M2_TO_FT2

    @property
    def D_main_ft(self) -> float:
        return self.D_main_m * M_TO_FT

    @property
    def D_main_in(self) -> float:
        return self.D_main_m * M_TO_IN


# -----------------------------
# Core computations
# -----------------------------

def compute_single(g: float, m: float, rho_air: float, Cd: float, V: float) -> SingleResult:
    """Return (S_total, D_total) for a single round canopy.
    S = (2 g m)/(rho C_d V^2),  D = sqrt(4 S / π)
    """
    if any(x <= 0 for x in (g, m, rho_air, Cd, V)):
        raise ValueError("All inputs must be positive.")
    S_total = (2.0 * g * m) / (rho_air * Cd * V * V)
    D_total = math.sqrt(4.0 * S_total / PI)
    return SingleResult(S_total_m2=S_total, D_total_m=D_total)


def compute_dual(
    g: float,
    m: float,
    rho_air: float,
    Cd_drogue: float,
    Cd_main: float,
    V: float,
    drogue_fraction: float = 0.20,
) -> DualResult:
    """Compute total, drogue, and main sizes for dual-deployment.

    The total area S_total is sized using an average C_d = (Cd_drogue + Cd_main)/2
    at the specified target terminal velocity V. The total is then split by
    drogue_fraction (default 0.20) to obtain drogue and main sub-areas.
    """
    if any(x <= 0 for x in (g, m, rho_air, Cd_drogue, Cd_main, V)):
        raise ValueError("All inputs must be positive.")
    if not (0.01 <= drogue_fraction <= 0.9):
        raise ValueError("Drogue fraction should be in [0.01, 0.90].")

    Cd_avg = 0.5 * (Cd_drogue + Cd_main)
    S_total = (2.0 * g * m) / (rho_air * Cd_avg * V * V)
    D_total = math.sqrt(4.0 * S_total / PI)

    S_drogue = S_total * drogue_fraction
    S_main   = S_total * (1.0 - drogue_fraction)

    D_drogue = math.sqrt(4.0 * S_drogue / PI)
    D_main   = math.sqrt(4.0 * S_main   / PI)

    return DualResult(
        S_total_m2=S_total,
        D_total_m=D_total,
        S_drogue_m2=S_drogue,
        D_drogue_m=D_drogue,
        S_main_m2=S_main,
        D_main_m=D_main,
    )


# -----------------------------
# Utility: rounding helpers
# -----------------------------
class FootRounding:
    NONE = "None"
    NEAREST = "Nearest whole ft"
    UP = "Ceil (next ft)"
    DOWN = "Floor (whole ft)"


def round_feet(value_ft: float, mode: str) -> float:
    if mode == FootRounding.NEAREST:
        return float(int(round(value_ft)))
    if mode == FootRounding.UP:
        return float(int(math.ceil(value_ft)))
    if mode == FootRounding.DOWN:
        return float(int(math.floor(value_ft)))
    return value_ft


# -----------------------------
# Qt Widgets
# -----------------------------
class LabeledSpin(QtWidgets.QDoubleSpinBox):
    def __init__(self, minimum: float, maximum: float, step: float, value: float, suffix: str = "", decimals: int = 3):
        super().__init__()
        self.setRange(minimum, maximum)
        self.setDecimals(decimals)
        self.setSingleStep(step)
        self.setValue(value)
        if suffix:
            self.setSuffix(f" {suffix}")


class ParachuteGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parachute Designer — QtPy")
        self.setMinimumWidth(760)
        self._build_ui()

    # ---- UI construction ----
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Mode + safety factor + rounding controls
        mode_box = QtWidgets.QGroupBox("Configuration")
        mode_layout = QtWidgets.QGridLayout(mode_box)

        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["single", "dual"])

        self.safety_spin = LabeledSpin(1.0, 5.0, 0.05, 1.10, suffix="×", decimals=2)
        self.round_combo = QtWidgets.QComboBox()
        self.round_combo.addItems([FootRounding.NONE, FootRounding.NEAREST, FootRounding.UP, FootRounding.DOWN])

        self.drogue_frac_spin = LabeledSpin(0.01, 0.90, 0.01, 0.20, suffix=" (fraction)", decimals=2)

        mode_layout.addWidget(QtWidgets.QLabel("Deployment mode"), 0, 0)
        mode_layout.addWidget(self.mode_combo, 0, 1)
        mode_layout.addWidget(QtWidgets.QLabel("Safety factor"), 0, 2)
        mode_layout.addWidget(self.safety_spin, 0, 3)
        mode_layout.addWidget(QtWidgets.QLabel("Diameter rounding"), 0, 4)
        mode_layout.addWidget(self.round_combo, 0, 5)
        mode_layout.addWidget(QtWidgets.QLabel("Drogue fraction (dual)"), 1, 0)
        mode_layout.addWidget(self.drogue_frac_spin, 1, 1)

        # Inputs
        inputs_box = QtWidgets.QGroupBox("Inputs")
        form = QtWidgets.QFormLayout(inputs_box)

        self.g_spin = LabeledSpin(1.0, 20.0, 0.01, 9.81, suffix="m/s²")
        self.m_spin = LabeledSpin(0.01, 1000.0, 0.1, 10.0, suffix="kg")
        self.rho_spin = LabeledSpin(0.1, 2.0, 0.01, 1.225, suffix="kg/m³")
        self.cd_spin = LabeledSpin(0.2, 2.5, 0.05, 1.20)
        self.cd_drogue_spin = LabeledSpin(0.2, 2.5, 0.05, 1.20)
        self.cd_main_spin = LabeledSpin(0.2, 2.5, 0.05, 1.20)
        self.v_spin = LabeledSpin(0.5, 30.0, 0.1, 10.0, suffix="m/s")

        form.addRow("g (gravitational acceleration)", self.g_spin)
        form.addRow("m (dry mass)", self.m_spin)
        form.addRow("rho_air (air density)", self.rho_spin)

        # The Cd input that is shown depends on mode; we add both and toggle visibility
        self.cd_row_single = QtWidgets.QWidget()
        cd_row_layout = QtWidgets.QHBoxLayout(self.cd_row_single)
        cd_row_layout.setContentsMargins(0,0,0,0)
        cd_row_layout.addWidget(QtWidgets.QLabel("C_d (single)"))
        cd_row_layout.addWidget(self.cd_spin)

        self.cd_row_dual = QtWidgets.QWidget()
        cd_dual_layout = QtWidgets.QHBoxLayout(self.cd_row_dual)
        cd_dual_layout.setContentsMargins(0,0,0,0)
        cd_dual_layout.addWidget(QtWidgets.QLabel("C_d_drogue / C_d_main"))
        cd_dual_layout.addWidget(self.cd_drogue_spin)
        cd_dual_layout.addWidget(self.cd_main_spin)

        form.addRow(self.cd_row_single)
        form.addRow(self.cd_row_dual)

        form.addRow("V (target descent rate)", self.v_spin)

        # Compute + warnings
        self.warn_label = QtWidgets.QLabel()
        palette = self.warn_label.palette()
        palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.darkYellow)
        self.warn_label.setPalette(palette)

        self.compute_btn = QtWidgets.QPushButton("Compute")
        self.compute_btn.setDefault(True)

        # Outputs table
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Stage",
            "Area [m²]",
            "Area [ft²]",
            "D [m]",
            "D [in]",
            "D [ft] (rounded)",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Layout assembly
        layout.addWidget(mode_box)
        layout.addWidget(inputs_box)
        layout.addWidget(self.compute_btn)
        layout.addWidget(self.warn_label)
        layout.addWidget(self.table, stretch=1)

        # Signals
        self.mode_combo.currentTextChanged.connect(self._sync_mode)
        self.compute_btn.clicked.connect(self._on_compute)
        self._sync_mode(self.mode_combo.currentText())

    # ---- Behaviour ----
    def _sync_mode(self, mode: str):
        is_single = (mode == "single")
        self.cd_row_single.setVisible(is_single)
        self.cd_row_dual.setVisible(not is_single)
        self.drogue_frac_spin.setEnabled(not is_single)

    def _set_warning(self, text: str | None):
        self.warn_label.setText(text or "")

    def _on_compute(self):
        try:
            mode = self.mode_combo.currentText()
            safety = float(self.safety_spin.value())
            rounding_mode = self.round_combo.currentText()
            g = float(self.g_spin.value())
            m = float(self.m_spin.value())
            rho = float(self.rho_spin.value())
            V = float(self.v_spin.value())

            self._set_warning(None)
            self.table.setRowCount(0)

            if mode == "single":
                Cd = float(self.cd_spin.value())
                res = compute_single(g, m, rho, Cd, V)
                self._populate_single(res, safety, rounding_mode)
            else:
                Cd_d = float(self.cd_drogue_spin.value())
                Cd_m = float(self.cd_main_spin.value())
                f = float(self.drogue_frac_spin.value())
                res = compute_dual(g, m, rho, Cd_d, Cd_m, V, drogue_fraction=f)
                self._populate_dual(res, safety, rounding_mode)

            # Advisory if descent speed is high
            if V >= 15.0:
                self._set_warning("Advisory: V ≥ 15 m/s is on the high side for safe recovery. Consider a lower target if structurally permissible.")

        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", str(exc))

    # ---- Table population helpers ----
    def _add_row(self, stage: str, area_m2: float, diam_m: float, rounding_mode: str, safety: float):
        area_ft2 = area_m2 * M2_TO_FT2
        diam_in = diam_m * M_TO_IN
        diam_ft = diam_m * M_TO_FT

        # Safety-factored diameter is based on diameter scaling with sqrt(area) => multiply by sqrt(safety)
        diam_ft_sf = diam_ft * math.sqrt(safety)

        # Apply rounding for purchase size in feet if ≥ 1 ft; otherwise show inches rounded to whole inch
        rounded_display = ""
        if diam_ft_sf >= 1.0:
            diam_ft_purchase = round_feet(diam_ft_sf, rounding_mode)
            rounded_display = f"{diam_ft_purchase:.0f} ft"
        else:
            inches_purchase = round(diam_in * math.sqrt(safety))
            rounded_display = f"< 1 ft (≈ {inches_purchase:.0f} in)"

        r = self.table.rowCount()
        self.table.insertRow(r)
        def item(text: str) -> QtWidgets.QTableWidgetItem:
            it = QtWidgets.QTableWidgetItem(text)
            it.setTextAlignment(QtCore.Qt.AlignCenter)
            return it

        self.table.setItem(r, 0, item(stage))
        self.table.setItem(r, 1, item(f"{area_m2:.3f}"))
        self.table.setItem(r, 2, item(f"{area_ft2:.3f}"))
        self.table.setItem(r, 3, item(f"{diam_m:.3f}"))
        self.table.setItem(r, 4, item(f"{diam_in:.1f}"))
        self.table.setItem(r, 5, item(rounded_display))

    def _populate_single(self, res: SingleResult, safety: float, rounding_mode: str):
        self._add_row("Total", res.S_total_m2, res.D_total_m, rounding_mode, safety)

    def _populate_dual(self, res: DualResult, safety: float, rounding_mode: str):
        self._add_row("Total", res.S_total_m2, res.D_total_m, rounding_mode, safety)
        self._add_row("Drogue", res.S_drogue_m2, res.D_drogue_m, rounding_mode, safety)
        self._add_row("Main", res.S_main_m2, res.D_main_m, rounding_mode, safety)


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = ParachuteGUI()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
