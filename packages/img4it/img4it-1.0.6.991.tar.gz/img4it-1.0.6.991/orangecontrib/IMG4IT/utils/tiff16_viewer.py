# -*- coding: utf-8 -*-
"""
Viewer TIFF 16 bits avec réglage d'étalement, zoom/pan
+ modes: linéaire, gamma 0.5, gamma 2.0, sigmoide,
         log, inverse-log, exponentielle, racine √, racine ³,
         HE (global), CLAHE (local via scikit-image si dispo),
         Wallis (local), Canny (edges via scikit-image si dispo)

NOUVEAU:
- Checkbox "Relative Min/Max (%)":
    OFF: spec/affichage en Min (I16) / Max (I16) (comportement actuel)
    ON : spec/affichage en Min(%) / Max(%) (valeurs des sliders)
         => transform_tiff16_to_tiff8 recalcule Min/Max I16 à chaque image, à partir de ces percentiles

Le champ de texte en bas affiche une spec complète "Transform | ..." réutilisable en batch.

Dépendances: AnyQt, numpy, tifffile, scipy
Optionnel: scikit-image (CLAHE + Canny)
"""
import sys
import os
import re
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import tifffile as tiff
from AnyQt import QtWidgets, QtGui, QtCore
from scipy.ndimage import uniform_filter

# --- CLAHE + Canny optionnels via scikit-image ---
try:
    from skimage import exposure as sk_exposure
    from skimage import feature as sk_feature
    HAS_SKIMAGE = True
except Exception:
    HAS_SKIMAGE = False

if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.IMG4IT.utils.reacalage_image import apply_transform_to_image_file
else:
    from orangecontrib.IMG4IT.utils.reacalage_image import apply_transform_to_image_file


# -------------------------------
# Safe cast helpers (évite float(None))
# -------------------------------
def _safe_float(x):
    return float(x) if x is not None else None


def _safe_int(x):
    return int(x) if x is not None else None


# -------------------------------
# Utils image / histogramme
# -------------------------------
def qimage_from_gray_uint8(arr_u8: np.ndarray) -> QtGui.QImage:
    """Convertit un ndarray uint8 (H, W) en QImage Grayscale8 sans copie."""
    if arr_u8.dtype != np.uint8 or arr_u8.ndim != 2:
        raise ValueError("qimage_from_gray_uint8 attend un array (H, W) en uint8.")
    if not arr_u8.flags["C_CONTIGUOUS"]:
        arr_u8 = np.ascontiguousarray(arr_u8)
    h, w = arr_u8.shape
    bytes_per_line = arr_u8.strides[0]
    qimg = QtGui.QImage(arr_u8.data, w, h, bytes_per_line,
                        QtGui.QImage.Format.Format_Grayscale8)
    qimg._arr_ref = arr_u8  # garder réf vivante
    return qimg


def hist_uint16(arr_u16: np.ndarray) -> np.ndarray:
    return np.bincount(arr_u16.ravel(), minlength=65536)


def percentile_from_hist(hist: np.ndarray, total_px: int, p: float) -> int:
    """Retourne une valeur 16 bits au percentile p en s'appuyant sur l'histogramme 65536 bins."""
    if p <= 0:
        return 0
    if p >= 100:
        return 65535
    target = total_px * (p / 100.0)
    cdf = np.cumsum(hist, dtype=np.int64)
    idx = int(np.searchsorted(cdf, target, side="left"))
    return int(np.clip(idx, 0, 65535))


def compute_low_high_from_percentiles(arr16: np.ndarray, low_p: int, high_p: int) -> Tuple[int, int]:
    """Calcule (lv,hv) I16 depuis percentiles sur l'image donnée."""
    arr16 = np.ascontiguousarray(arr16)
    h = hist_uint16(arr16)
    total_px = int(arr16.size)
    lv = percentile_from_hist(h, total_px, float(low_p))
    hv = percentile_from_hist(h, total_px, float(high_p))
    if hv <= lv:
        hv = min(lv + 1, 65535)
    return int(lv), int(hv)


# -------------------------------
# HE / CLAHE / Wallis
# -------------------------------
def he_on_unit_float(t: np.ndarray, nbins: int = 256) -> np.ndarray:
    t = np.clip(t.astype(np.float32), 0.0, 1.0)
    hh, bins = np.histogram(t, bins=int(max(2, nbins)), range=(0.0, 1.0))
    cdf = np.cumsum(hh).astype(np.float32)
    if cdf[-1] <= 0:
        return t
    cdf /= cdf[-1]
    bin_centers = (bins[:-1] + bins[1:]) * 0.5
    y = np.interp(t.ravel(), bin_centers, cdf).reshape(t.shape).astype(np.float32)
    return y


def wallis_filter(t: np.ndarray, win_size: int,
                  mu_target: float = 50.0, sigma_target: float = 30.0) -> np.ndarray:
    """
    Wallis filter sur image normalisée t ∈ [0,1].
    mu_target/sigma_target en échelle 0..255.
    """
    t = t.astype(np.float32)

    local_mean = uniform_filter(t, size=win_size, mode="reflect")
    local_mean_sq = uniform_filter(t * t, size=win_size, mode="reflect")
    local_var = np.maximum(local_mean_sq - local_mean * local_mean, 1e-6)
    local_std = np.sqrt(local_var, dtype=np.float32)

    mu_c = mu_target / 255.0
    sigma_c = sigma_target / 255.0
    y = (t - local_mean) * (sigma_c / (local_std + 1e-6)) + mu_c
    return np.clip(y, 0.0, 1.0).astype(np.float32)


def clahe_on_unit_float(t: np.ndarray, clip_limit: float = 0.01, nbins: int = 256) -> np.ndarray:
    t = np.clip(t.astype(np.float32), 0.0, 1.0)
    if HAS_SKIMAGE:
        y = sk_exposure.equalize_adapthist(
            t,
            clip_limit=float(max(1e-6, clip_limit)),
            nbins=int(max(2, nbins)),
        )
        return y.astype(np.float32, copy=False)
    return he_on_unit_float(t, nbins=nbins)


# -------------------------------
# Viewer
# -------------------------------
class ImageView(QtWidgets.QGraphicsView):
    """Widget avec zoom + pan à la souris + émission des coords souris."""
    mouseMoved = QtCore.Signal(int, int)  # (col, row)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.viewport().setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self._img_w = 0
        self._img_h = 0
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.viewport().installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self.viewport() and ev.type() == QtCore.QEvent.CursorChange:
            if self.viewport().cursor().shape() != QtCore.Qt.CrossCursor:
                QtCore.QTimer.singleShot(0, lambda: self.viewport().setCursor(QtCore.Qt.CrossCursor))
                return True
        return super().eventFilter(obj, ev)

    def set_image_size(self, w: int, h: int):
        self._img_w = int(max(0, w))
        self._img_h = int(max(0, h))

    def wheelEvent(self, event: QtGui.QWheelEvent):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        f = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        self.scale(f, f)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        sp = self.mapToScene(event.pos())
        x = int(np.floor(sp.x()))
        y = int(np.floor(sp.y()))
        if 0 <= x < self._img_w and 0 <= y < self._img_h:
            self.mouseMoved.emit(x, y)
        else:
            self.mouseMoved.emit(-1, -1)
        super().mouseMoveEvent(event)


class Tiff16Viewer(QtWidgets.QWidget):
    def __init__(self, input_path, parent=None):
        super().__init__(parent)

        # --- Résolution dossier / liste images ---
        self.files: List[str] = []
        self.idx = 0
        self._resolve_inputs(input_path)

        # --- État image ---
        self.arr16: Optional[np.ndarray] = None
        self.h = self.w = 0
        self.hist: Optional[np.ndarray] = None
        self.total_px = 0
        self.min_val = 0
        self.max_val = 0
        self._last_img8: Optional[np.ndarray] = None
        self._last_transform_spec: str = ""

        # --- Scene / view ---
        self.scene = QtWidgets.QGraphicsScene()
        self.view = ImageView()
        self.view.setScene(self.scene)
        self.pixmap_item = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        # --- Bandeau nom fichier ---
        self.name_label = QtWidgets.QLabel("--")
        self.name_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)

        nav = QtWidgets.QHBoxLayout()
        nav.addStretch(1)
        nav.addWidget(self.name_label)

        # --- Coordonnées souris ---
        self.col_edit = QtWidgets.QLineEdit()
        self.col_edit.setReadOnly(True)
        self.col_edit.setFixedWidth(90)
        self.col_edit.setPlaceholderText("Colonne")

        self.row_edit = QtWidgets.QLineEdit()
        self.row_edit.setReadOnly(True)
        self.row_edit.setFixedWidth(90)
        self.row_edit.setPlaceholderText("Ligne")

        self.val_edit = QtWidgets.QLineEdit()
        self.val_edit.setReadOnly(True)
        self.val_edit.setFixedWidth(140)
        self.val_edit.setPlaceholderText("Valeur 16b → 8b")

        coords = QtWidgets.QHBoxLayout()
        coords.addWidget(QtWidgets.QLabel("Col:"))
        coords.addWidget(self.col_edit)
        coords.addSpacing(8)
        coords.addWidget(QtWidgets.QLabel("Ligne:"))
        coords.addWidget(self.row_edit)
        coords.addSpacing(8)
        coords.addWidget(QtWidgets.QLabel("Valeur:"))
        coords.addWidget(self.val_edit)
        coords.addStretch(1)

        # --- Sliders percentiles ---
        self.low_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.high_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        for s in (self.low_slider, self.high_slider):
            s.setRange(0, 100)
            s.setTickInterval(5)
            s.setSingleStep(1)
            s.setTracking(True)
        self.low_slider.setValue(2)
        self.high_slider.setValue(98)

        self.low_spin = QtWidgets.QSpinBox()
        self.low_spin.setRange(0, 100)
        self.low_spin.setSuffix(" %")
        self.high_spin = QtWidgets.QSpinBox()
        self.high_spin.setRange(0, 100)
        self.high_spin.setSuffix(" %")
        self.low_spin.setValue(self.low_slider.value())
        self.high_spin.setValue(self.high_slider.value())

        # --- Boutons d'étendue ---
        self.btn_auto = QtWidgets.QPushButton("Auto (2–98%)")
        self.btn_full = QtWidgets.QPushButton("Plein écart (min–max)")
        self.btn_reset = QtWidgets.QPushButton("Réinitialiser vue")

        # --- Boutons contraste ---
        self.btn_lin = QtWidgets.QPushButton("Lineaire")
        self.btn_gam05 = QtWidgets.QPushButton("Gamma 0.5")
        self.btn_gam20 = QtWidgets.QPushButton("Gamma 2.0")
        self.btn_sig = QtWidgets.QPushButton("Sigmoide")

        self.btn_log = QtWidgets.QPushButton("Log")
        self.btn_invlog = QtWidgets.QPushButton("Inverse-Log")
        self.btn_exp = QtWidgets.QPushButton("Exponentielle")
        self.btn_sqrt = QtWidgets.QPushButton("Racine carree")
        self.btn_cbrt = QtWidgets.QPushButton("Racine cubique")
        self.btn_he = QtWidgets.QPushButton("HE (global)")
        self.btn_clahe = QtWidgets.QPushButton("CLAHE")

        # --- Wallis ---
        self.btn_wallis = QtWidgets.QPushButton("Wallis")
        self.wallis_win_spin = QtWidgets.QSpinBox()
        self.wallis_win_spin.setRange(3, 101)
        self.wallis_win_spin.setSingleStep(2)
        self.wallis_win_spin.setValue(15)

        self.wallis_mu_spin = QtWidgets.QSpinBox()
        self.wallis_mu_spin.setRange(0, 255)
        self.wallis_mu_spin.setValue(127)

        self.wallis_sigma_spin = QtWidgets.QSpinBox()
        self.wallis_sigma_spin.setRange(0, 255)
        self.wallis_sigma_spin.setValue(35)

        # --- HE/CLAHE params ---
        self.he_bins_spin = QtWidgets.QSpinBox()
        self.he_bins_spin.setRange(16, 4096)
        self.he_bins_spin.setSingleStep(16)
        self.he_bins_spin.setValue(256)

        self.clahe_clip_spin = QtWidgets.QDoubleSpinBox()
        self.clahe_clip_spin.setRange(0.001, 0.100)
        self.clahe_clip_spin.setSingleStep(0.001)
        self.clahe_clip_spin.setDecimals(3)
        self.clahe_clip_spin.setValue(0.010)

        # --- Canny ---
        self.btn_canny = QtWidgets.QPushButton("Canny")
        self.btn_canny.setEnabled(HAS_SKIMAGE)
        self.canny_sigma_spin = QtWidgets.QDoubleSpinBox()
        self.canny_sigma_spin.setRange(0.1, 10.0)
        self.canny_sigma_spin.setSingleStep(0.1)
        self.canny_sigma_spin.setDecimals(1)
        self.canny_sigma_spin.setValue(1.2)

        self.canny_low_spin = QtWidgets.QDoubleSpinBox()
        self.canny_low_spin.setRange(0.0, 1.0)
        self.canny_low_spin.setSingleStep(0.01)
        self.canny_low_spin.setDecimals(2)
        self.canny_low_spin.setValue(0.08)

        self.canny_high_spin = QtWidgets.QDoubleSpinBox()
        self.canny_high_spin.setRange(0.0, 1.0)
        self.canny_high_spin.setSingleStep(0.01)
        self.canny_high_spin.setDecimals(2)
        self.canny_high_spin.setValue(0.20)

        # --- Checkbox Relative Min/Max ---
        self.chk_relative_minmax = QtWidgets.QCheckBox("Relative Min/Max (%)")
        self.chk_relative_minmax.setChecked(False)
        self.chk_relative_minmax.setToolTip(
            "OFF: spec/affichage en Min/Max I16 (comportement actuel)\n"
            "ON : spec/affichage en Min/Max percentiles (sliders) -> recalcule Min/Max I16 à chaque image en batch."
        )

        # --- Mode courant ---
        self.contrast_mode = "linear"

        # --- Layouts ---
        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Percentile bas"), 0, 0)
        grid.addWidget(self.low_slider, 0, 1)
        grid.addWidget(self.low_spin, 0, 2)
        grid.addWidget(QtWidgets.QLabel("Percentile haut"), 1, 0)
        grid.addWidget(self.high_slider, 1, 1)
        grid.addWidget(self.high_spin, 1, 2)

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.btn_auto)
        btns.addWidget(self.btn_full)
        btns.addWidget(self.btn_reset)
        btns.addStretch(1)

        contrast_btns1 = QtWidgets.QHBoxLayout()
        contrast_btns1.addWidget(QtWidgets.QLabel("Courbe contraste :"))
        for b in (self.btn_lin, self.btn_gam05, self.btn_gam20, self.btn_sig):
            contrast_btns1.addWidget(b)
        contrast_btns1.addStretch(1)

        contrast_btns2 = QtWidgets.QHBoxLayout()
        for b in (self.btn_log, self.btn_invlog, self.btn_exp, self.btn_sqrt, self.btn_cbrt, self.btn_he, self.btn_clahe):
            contrast_btns2.addWidget(b)
        contrast_btns2.addWidget(self.btn_wallis)
        contrast_btns2.addWidget(self.btn_canny)
        contrast_btns2.addStretch(1)

        params_row = QtWidgets.QHBoxLayout()
        params_row.addWidget(QtWidgets.QLabel("HE nbins:"))
        params_row.addWidget(self.he_bins_spin)
        params_row.addSpacing(12)
        params_row.addWidget(QtWidgets.QLabel("CLAHE clip:"))
        params_row.addWidget(self.clahe_clip_spin)

        params_row.addSpacing(12)
        params_row.addWidget(QtWidgets.QLabel("Wallis win:"))
        params_row.addWidget(self.wallis_win_spin)
        params_row.addSpacing(6)
        params_row.addWidget(QtWidgets.QLabel("Wallis mean:"))
        params_row.addWidget(self.wallis_mu_spin)
        params_row.addSpacing(6)
        params_row.addWidget(QtWidgets.QLabel("Wallis std:"))
        params_row.addWidget(self.wallis_sigma_spin)

        params_row.addSpacing(12)
        params_row.addWidget(QtWidgets.QLabel("Canny σ:"))
        params_row.addWidget(self.canny_sigma_spin)
        params_row.addSpacing(6)
        params_row.addWidget(QtWidgets.QLabel("low:"))
        params_row.addWidget(self.canny_low_spin)
        params_row.addSpacing(6)
        params_row.addWidget(QtWidgets.QLabel("high:"))
        params_row.addWidget(self.canny_high_spin)

        params_row.addSpacing(12)
        params_row.addWidget(self.chk_relative_minmax)
        params_row.addStretch(1)

        # --- Panneau d'infos (spec) ---
        self.info_edit = QtWidgets.QLineEdit()
        self.info_edit.setReadOnly(True)
        self.info_edit.setPlaceholderText("Transform | ...")

        v = QtWidgets.QVBoxLayout(self)
        v.addLayout(nav)
        v.addWidget(self.view, stretch=1)
        v.addLayout(coords)
        v.addLayout(grid)
        v.addLayout(btns)
        v.addLayout(contrast_btns1)
        v.addLayout(contrast_btns2)
        v.addLayout(params_row)
        v.addWidget(self.info_edit)

        # --- Connexions ---
        self.low_slider.valueChanged.connect(self._on_low_slider)
        self.high_slider.valueChanged.connect(self._on_high_slider)
        self.low_spin.valueChanged.connect(self._on_low_spin)
        self.high_spin.valueChanged.connect(self._on_high_spin)

        self.btn_auto.clicked.connect(self.apply_auto)
        self.btn_full.clicked.connect(self.apply_full)
        self.btn_reset.clicked.connect(self.reset_view)

        self.btn_lin.clicked.connect(lambda: self.set_contrast_mode("linear"))
        self.btn_gam05.clicked.connect(lambda: self.set_contrast_mode("gamma05"))
        self.btn_gam20.clicked.connect(lambda: self.set_contrast_mode("gamma20"))
        self.btn_sig.clicked.connect(lambda: self.set_contrast_mode("sigmoid"))

        self.btn_log.clicked.connect(lambda: self.set_contrast_mode("log"))
        self.btn_invlog.clicked.connect(lambda: self.set_contrast_mode("invlog"))
        self.btn_exp.clicked.connect(lambda: self.set_contrast_mode("exp"))
        self.btn_sqrt.clicked.connect(lambda: self.set_contrast_mode("sqrt"))
        self.btn_cbrt.clicked.connect(lambda: self.set_contrast_mode("cbrt"))
        self.btn_he.clicked.connect(lambda: self.set_contrast_mode("he"))
        self.btn_clahe.clicked.connect(lambda: self.set_contrast_mode("clahe"))

        self.btn_wallis.clicked.connect(lambda: self.set_contrast_mode("wallis"))
        self.btn_canny.clicked.connect(lambda: self.set_contrast_mode("canny"))

        self.he_bins_spin.valueChanged.connect(self.update_view)
        self.clahe_clip_spin.valueChanged.connect(self.update_view)
        self.wallis_win_spin.valueChanged.connect(self.update_view)
        self.wallis_mu_spin.valueChanged.connect(self.update_view)
        self.wallis_sigma_spin.valueChanged.connect(self.update_view)

        self.canny_sigma_spin.valueChanged.connect(self.update_view)
        self.canny_low_spin.valueChanged.connect(self.update_view)
        self.canny_high_spin.valueChanged.connect(self.update_view)

        self.chk_relative_minmax.stateChanged.connect(self.update_view)

        self.view.mouseMoved.connect(self._on_mouse_moved)

        # --- Charge première image ---
        self._load_current_image()

    # -----------------------
    # Spec builder (inclut tout)
    # -----------------------
    def build_transform_spec_from_ui(self, low_val_i16: int, high_val_i16: int) -> str:
        """
        Construit une spec "Transform | ..." complète, cohérente avec l'état UI.
        - Relative OFF -> Min(I16)/Max(I16)
        - Relative ON  -> Min(%)/Max(%)
        Inclut paramètres du mode (HE/CLAHE/Wallis/Canny).
        """
        parts = ["Transform"]

        if self.chk_relative_minmax.isChecked():
            parts.append(f"Min(%) = {int(self.low_slider.value())}")
            parts.append(f"Max(%) = {int(self.high_slider.value())}")
        else:
            parts.append(f"Min (I16) = {int(low_val_i16)}")
            parts.append(f"Max (I16) = {int(high_val_i16)}")

        parts.append(f"Mode = {self._human_mode_name()}")

        if self.contrast_mode == "he":
            parts.append(f"HE bins = {int(self.he_bins_spin.value())}")

        elif self.contrast_mode == "clahe":
            parts.append(f"HE bins = {int(self.he_bins_spin.value())}")
            parts.append(f"CLAHE clip = {float(self.clahe_clip_spin.value()):.3f}")

        elif self.contrast_mode == "wallis":
            parts.append(f"Wallis average={int(self.wallis_mu_spin.value())}")
            parts.append(f"standard deviation={int(self.wallis_sigma_spin.value())}")
            parts.append(f"win_size={int(self.wallis_win_spin.value())}")

        elif self.contrast_mode == "canny":
            parts.append(f"Canny sigma={float(self.canny_sigma_spin.value()):.1f}")
            parts.append(f"low={float(self.canny_low_spin.value()):.2f}")
            parts.append(f"high={float(self.canny_high_spin.value()):.2f}")

        return " | ".join(parts)

    def get_last_transform_spec(self) -> str:
        return self._last_transform_spec

    def _human_mode_name(self) -> str:
        mapping = {
            "linear": "Lineaire",
            "gamma05": "Gamma 0.5",
            "gamma20": "Gamma 2.0",
            "sigmoid": "Sigmoide",
            "log": "Logarithmique",
            "invlog": "Inverse-Log",
            "exp": "Exponentielle",
            "sqrt": "Racine carree",
            "cbrt": "Racine cubique",
            "he": "HE (global)",
            "clahe": "CLAHE",
            "wallis": "Wallis",
            "canny": "Canny (edges)",
        }
        return mapping.get(self.contrast_mode, self.contrast_mode)

    def _update_info_panel(self, low_val_i16: int, high_val_i16: int):
        # On affiche exactement la spec complète (réutilisable)
        spec = self.build_transform_spec_from_ui(low_val_i16, high_val_i16)
        self._last_transform_spec = spec
        self.info_edit.setText(spec)

    # -----------------------
    # Inputs / load
    # -----------------------
    def _resolve_inputs(self, input_path):
        path = os.path.abspath(input_path)
        if os.path.isdir(path):
            folder = path
            start_file = None
        else:
            folder = os.path.dirname(path) if os.path.dirname(path) else "."
            start_file = os.path.basename(path)

        exts = {".tif", ".tiff"}
        files = [f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in exts]
        files.sort(key=lambda x: x.lower())

        if not files:
            QtWidgets.QMessageBox.critical(None, "Erreur", f"Aucune image .tif/.tiff dans :\n{folder}")
            sys.exit(1)

        self.files = [os.path.join(folder, f) for f in files]

        if start_file:
            try:
                self.idx = files.index(start_file)
            except ValueError:
                self.idx = 0
        else:
            self.idx = 0

    def _load_current_image(self):
        path = self.files[self.idx]
        self._load_image_from_path(path)
        self.view.resetTransform()
        self.update_view()
        self._update_name_label()

    def _load_image_from_path(self, path):
        arr = tiff.imread(path)
        if arr.ndim == 3:
            arr = arr[..., 0]
        if arr.dtype != np.uint16:
            arr = arr.astype(np.uint16, copy=False)
        self.arr16 = np.ascontiguousarray(arr)
        self.h, self.w = self.arr16.shape

        self.hist = hist_uint16(self.arr16)
        self.total_px = int(self.arr16.size)
        self.min_val = int(self.arr16.min())
        self.max_val = int(self.arr16.max())

        self.scene.setSceneRect(0, 0, self.w, self.h)
        self.view.set_image_size(self.w, self.h)

    def _update_name_label(self):
        self.name_label.setText(os.path.basename(self.files[self.idx]))

    # -----------------------
    # Contrast pipeline
    # -----------------------
    def set_contrast_mode(self, mode: str):
        self.contrast_mode = mode
        self.update_view()

    def compute_low_high_values_i16(self) -> Tuple[int, int]:
        low_p, high_p = int(self.low_slider.value()), int(self.high_slider.value())
        if high_p <= low_p:
            high_p = min(low_p + 1, 100)
            for w, val in ((self.high_slider, high_p), (self.high_spin, high_p)):
                w.blockSignals(True)
                w.setValue(val)
                w.blockSignals(False)

        lv = percentile_from_hist(self.hist, self.total_px, low_p)
        hv = percentile_from_hist(self.hist, self.total_px, high_p)
        if hv <= lv:
            hv = min(lv + 1, 65535)
        return int(lv), int(hv)

    @staticmethod
    def apply_curve_pointwise(t: np.ndarray, mode: str) -> np.ndarray:
        if mode == "linear":
            y = t
        elif mode == "gamma05":
            y = np.power(t, 0.5, dtype=np.float32)
        elif mode == "gamma20":
            y = np.power(t, 2.0, dtype=np.float32)
        elif mode == "sigmoid":
            gain = 10.0
            y = 1.0 / (1.0 + np.exp(-gain * (t - 0.5)))
            y = (y - y.min()) / max(1e-12, (y.max() - y.min()))
        elif mode == "log":
            c = 100.0
            y = np.log1p(c * t) / np.log1p(c)
        elif mode == "invlog":
            c = 4.0
            y = (np.expm1(c * t) / np.expm1(c)).astype(np.float32)
        elif mode == "exp":
            k = 0.7
            y = np.power(t, k, dtype=np.float32)
        elif mode == "sqrt":
            y = np.sqrt(t, dtype=np.float32)
        elif mode == "cbrt":
            y = np.power(t, 1.0 / 3.0, dtype=np.float32)
        elif mode == "wallis":
            y = wallis_filter(t, win_size=15)
        else:
            y = t
        return np.clip(y, 0.0, 1.0).astype(np.float32)

    def stretch_to_8bit(self, arr16: np.ndarray, lv: int, hv: int) -> np.ndarray:
        rng = float(max(1, hv - lv))
        t = (arr16.astype(np.int32) - lv) / rng
        t = np.clip(t, 0.0, 1.0).astype(np.float32)

        mode = self.contrast_mode

        if mode == "he":
            y = he_on_unit_float(t, nbins=int(self.he_bins_spin.value()))
            return np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)

        if mode == "clahe":
            y = clahe_on_unit_float(
                t,
                clip_limit=float(self.clahe_clip_spin.value()),
                nbins=int(self.he_bins_spin.value()),
            )
            return np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)

        if mode == "wallis":
            y = wallis_filter(
                t,
                win_size=int(self.wallis_win_spin.value()),
                mu_target=float(self.wallis_mu_spin.value()),
                sigma_target=float(self.wallis_sigma_spin.value()),
            )
            return np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)

        if mode == "canny":
            if not HAS_SKIMAGE:
                # fallback: image normalisée
                return np.clip(t * 255.0, 0.0, 255.0).astype(np.uint8)
            sigma = float(self.canny_sigma_spin.value())
            low = float(self.canny_low_spin.value())
            high = float(self.canny_high_spin.value())
            if high < low:
                high = low
            edges = sk_feature.canny(
                t,
                sigma=sigma,
                low_threshold=low,
                high_threshold=high,
            )
            return (edges.astype(np.uint8) * 255)

        y = self.apply_curve_pointwise(t, mode)
        return np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)

    # -----------------------
    # Render
    # -----------------------
    def update_view(self):
        low_val_i16, high_val_i16 = self.compute_low_high_values_i16()
        img8 = self.stretch_to_8bit(self.arr16, low_val_i16, high_val_i16)
        self._last_img8 = img8

        qimg = qimage_from_gray_uint8(img8)
        self.pixmap_item.setPixmap(QtGui.QPixmap.fromImage(qimg))

        extra = ""
        if self.contrast_mode in ("clahe", "canny") and not HAS_SKIMAGE:
            extra = " (skimage indisponible)"

        self.setWindowTitle(
            f"TIFF 16 bits – [{low_val_i16} .. {high_val_i16}] – {self.w}x{self.h} – "
            f"Mode: {self.contrast_mode}{extra}"
        )

        # zone bas = spec complète (incluant Relative si coché)
        self._update_info_panel(low_val_i16, high_val_i16)

    # -----------------------
    # Slots
    # -----------------------
    def _on_low_slider(self, val):
        self.low_spin.blockSignals(True)
        self.low_spin.setValue(val)
        self.low_spin.blockSignals(False)
        self.update_view()

    def _on_high_slider(self, val):
        if val <= self.low_slider.value():
            val = min(self.low_slider.value() + 1, 100)
            self.high_slider.blockSignals(True)
            self.high_slider.setValue(val)
            self.high_slider.blockSignals(False)
        self.high_spin.blockSignals(True)
        self.high_spin.setValue(val)
        self.high_spin.blockSignals(False)
        self.update_view()

    def _on_low_spin(self, val):
        self.low_slider.blockSignals(True)
        self.low_slider.setValue(val)
        self.low_slider.blockSignals(False)
        self.update_view()

    def _on_high_spin(self, val):
        if val <= self.low_spin.value():
            val = min(self.low_spin.value() + 1, 100)
            self.high_spin.blockSignals(True)
            self.high_spin.setValue(val)
            self.high_spin.blockSignals(False)
        self.high_slider.blockSignals(True)
        self.high_slider.setValue(val)
        self.high_slider.blockSignals(False)
        self.update_view()

    def _on_mouse_moved(self, col: int, row: int):
        if col < 0 or row < 0:
            self.col_edit.setText("")
            self.row_edit.setText("")
            self.val_edit.setText("")
            return

        self.col_edit.setText(str(col))
        self.row_edit.setText(str(row))

        try:
            v16 = int(self.arr16[row, col])
        except Exception:
            v16 = None

        v8 = None
        if self._last_img8 is not None:
            try:
                v8 = int(self._last_img8[row, col])
            except Exception:
                v8 = None

        if v16 is None:
            self.val_edit.setText("")
        else:
            self.val_edit.setText(f"{v16}" + (f" \u2192 {v8}" if v8 is not None else ""))

    def apply_auto(self):
        self.low_slider.setValue(2)
        self.high_slider.setValue(98)
        self.update_view()

    def apply_full(self):
        self.low_slider.setValue(0)
        self.high_slider.setValue(100)
        self.update_view()

    def reset_view(self):
        self.view.resetTransform()
        self.update_view()


def view_tiff_qt(input_path, parent=None):
    app = QtWidgets.QApplication.instance()
    owns_app = False
    if app is None:
        app = QtWidgets.QApplication(sys.argv[:1])
        owns_app = True

    w = Tiff16Viewer(input_path, parent=parent)
    w.resize(1200, 950)
    w.show()

    if owns_app:
        sys.exit(app.exec())

    return w


# -------------------------------
# Spec parsing / processing
# -------------------------------
def _normalize_mode_name(s: str) -> str:
    """Mappe un libellé humain -> code interne du viewer."""
    s0 = (s or "").strip().lower()
    s0 = (s0
          .replace("é", "e").replace("è", "e").replace("ê", "e")
          .replace("ï", "i").replace("î", "i")
          .replace("ô", "o").replace("ö", "o").replace("à", "a")
          .replace("ç", "c"))
    s0 = re.sub(r"\s+", " ", s0)

    aliases = {
        "lineaire": "linear",
        "linear": "linear",
        "gamma 0.5": "gamma05",
        "gamma0.5": "gamma05",
        "gamma 2.0": "gamma20",
        "gamma2.0": "gamma20",
        "sigmoide": "sigmoid",
        "sigmoid": "sigmoid",
        "logarithmique": "log",
        "log": "log",
        "inverse-log": "invlog",
        "inverse log": "invlog",
        "exponentielle": "exp",
        "exp": "exp",
        "racine carree": "sqrt",
        "sqrt": "sqrt",
        "racine cubique": "cbrt",
        "cbrt": "cbrt",
        "he (global)": "he",
        "he": "he",
        "clahe": "clahe",
        "wallis": "wallis",
        "canny": "canny",
        "canny (edges)": "canny",
        "canny edges": "canny",
    }
    return aliases.get(s0, s0)


def _parse_transform_spec(spec: str) -> Dict[str, Any]:
    """
    Supporte:
      - Transform | Min (I16) = ... | Max (I16) = ... | Mode = ...
      - Transform | Min(%) = ... | Max(%) = ... | Mode = ...
    + params optionnels:
      HE bins = N
      CLAHE clip = x.xxx
      Wallis average=127 | standard deviation=35 | win_size=15
      Canny sigma=1.2 | low=0.08 | high=0.20
    """
    if not isinstance(spec, str):
        raise ValueError("transform_spec doit être une chaîne.")
    raw = spec.strip()

    # Mode (obligatoire)
    m_mode = re.search(r"Mode\s*=\s*([^\|]+)", raw, re.I)
    if not m_mode:
        raise ValueError("Chaîne invalide : impossible d'extraire Mode.")
    mode_human = m_mode.group(1).strip()
    mode = _normalize_mode_name(mode_human)

    # Min/Max I16
    m_min_i16 = re.search(r"Min\s*\(I16\)\s*=\s*(\d+)", raw, re.I)
    m_max_i16 = re.search(r"Max\s*\(I16\)\s*=\s*(\d+)", raw, re.I)

    # Min/Max %
    m_min_p = re.search(r"Min\s*\(%\)\s*=\s*(\d+)", raw, re.I)
    m_max_p = re.search(r"Max\s*\(%\)\s*=\s*(\d+)", raw, re.I)

    is_relative = bool(m_min_p and m_max_p)

    low_val = high_val = None
    low_p = high_p = None

    if is_relative:
        low_p = int(np.clip(int(m_min_p.group(1)), 0, 100))
        high_p = int(np.clip(int(m_max_p.group(1)), 0, 100))
        if high_p <= low_p:
            high_p = min(low_p + 1, 100)
    else:
        if not (m_min_i16 and m_max_i16):
            raise ValueError("Chaîne invalide : impossible d'extraire Min/Max (I16) ou Min/Max (%).")
        low_val = int(np.clip(int(m_min_i16.group(1)), 0, 65535))
        high_val = int(np.clip(int(m_max_i16.group(1)), low_val + 1, 65535))

    # HE bins
    he_bins = None
    m_bins = re.search(r"HE\s*bins\s*=\s*(\d+)", raw, re.I)
    if m_bins:
        he_bins = int(m_bins.group(1))

    # CLAHE clip
    clahe_clip = None
    m_clip = re.search(r"CLAHE\s*clip\s*=\s*([0-9]*\.?[0-9]+)", raw, re.I)
    if m_clip:
        clahe_clip = float(m_clip.group(1))

    # Wallis
    m_mu = re.search(r"(?:wallis\s*)?(?:average|mean|mu|moyenne)\s*=\s*([0-9]+(?:\.[0-9]+)?)", raw, re.I)
    m_sigma = re.search(r"(?:wallis\s*)?(?:standard\s*deviation|std|sigma|ecart\s*type)\s*=\s*([0-9]+(?:\.[0-9]+)?)", raw, re.I)
    m_win = re.search(r"(?:wallis\s*)?(?:win(?:_)?size|window(?:_)?size|fenetre|taille\s*fenetre)\s*=\s*(\d+)", raw, re.I)

    wallis_mu = float(m_mu.group(1)) if m_mu else None
    wallis_sigma = float(m_sigma.group(1)) if m_sigma else None
    wallis_win = int(m_win.group(1)) if m_win else None

    # Canny
    m_c_sigma = re.search(r"(?:canny\s*)?(?:sigma|σ)\s*=\s*([0-9]+(?:\.[0-9]+)?)", raw, re.I)
    m_c_low = re.search(r"(?:canny\s*)?low\s*=\s*([0-9]*\.?[0-9]+)", raw, re.I)
    m_c_high = re.search(r"(?:canny\s*)?high\s*=\s*([0-9]*\.?[0-9]+)", raw, re.I)

    canny_sigma = float(m_c_sigma.group(1)) if m_c_sigma else None
    canny_low = float(m_c_low.group(1)) if m_c_low else None
    canny_high = float(m_c_high.group(1)) if m_c_high else None

    return {
        "is_relative": is_relative,
        "low_val": low_val,
        "high_val": high_val,
        "low_p": low_p,
        "high_p": high_p,
        "mode_human": mode_human,
        "mode": mode,
        "he_bins": he_bins,
        "clahe_clip": clahe_clip,
        "wallis_mu": wallis_mu,
        "wallis_sigma": wallis_sigma,
        "wallis_win": wallis_win,
        "canny_sigma": canny_sigma,
        "canny_low": canny_low,
        "canny_high": canny_high,
    }


def _parse_crop_spec(spec: str) -> Tuple[int, int, int, int]:
    if not isinstance(spec, str):
        raise ValueError("crop_spec must be a string.")

    def get_int(pattern):
        m = re.search(pattern, spec, flags=re.I)
        return int(m.group(1)) if m else None

    line = get_int(r"\bline\s*=\s*(-?\d+)")
    col = get_int(r"\bcol\s*=\s*(-?\d+)")
    dline = get_int(r"\bdelta[_\s]*line\s*=\s*(\d+)")
    dcol = get_int(r"\bdelta[_\s]*col\s*=\s*(\d+)")

    if line is None or col is None or dline is None or dcol is None:
        raise ValueError(
            "Invalid crop spec. Expected: 'Crop | line = <int> | col = <int> | "
            "delta_line = <int> | delta_col = <int>'"
        )
    if dline <= 0 or dcol <= 0:
        raise ValueError("delta_line and delta_col must be positive integers.")
    return line, col, dline, dcol


def crop_tiff_by_spec(src_path: str, dst_path: str, crop_spec: str) -> Dict[str, Any]:
    arr = tiff.imread(src_path)

    if arr.ndim == 2:
        if arr.dtype not in (np.uint8, np.uint16):
            raise ValueError(f"Unsupported dtype for 2D image: {arr.dtype}")
        fmt = ("mono16" if arr.dtype == np.uint16 else "mono", arr.dtype)
    elif arr.ndim == 3:
        H, W, C = arr.shape
        if arr.dtype == np.uint8 and C in (3, 4):
            fmt = ("rgb" if C == 3 else "rgba", np.uint8)
        elif arr.dtype == np.uint8 and C == 1:
            arr = arr[..., 0]
            fmt = ("mono", np.uint8)
        else:
            raise ValueError(f"Unsupported 3D image shape/dtype: {arr.shape}, {arr.dtype}")
    else:
        raise ValueError(f"Unsupported image ndim: {arr.ndim}")

    H, W = arr.shape[:2]
    line, col, dline, dcol = _parse_crop_spec(crop_spec)

    y0 = max(0, line)
    x0 = max(0, col)
    y1 = min(H, y0 + dline)
    x1 = min(W, x0 + dcol)

    if y1 <= y0 or x1 <= x0:
        raise ValueError("Crop is empty after clamping to image bounds.")

    roi = np.ascontiguousarray(arr[y0:y1, x0:x1, ...])

    photometric = "minisblack" if fmt[0] in ("mono", "mono16") else "rgb"
    tiff.imwrite(dst_path, roi, photometric=photometric)

    return {
        "src": src_path,
        "dst": dst_path,
        "input_shape": tuple(arr.shape),
        "output_shape": tuple(roi.shape),
        "dtype": str(roi.dtype),
        "crop_requested": {"line": line, "col": col, "delta_line": dline, "delta_col": dcol},
        "crop_effective": {"y0": int(y0), "x0": int(x0), "y1": int(y1), "x1": int(x1)},
    }


def _which_op(spec: str) -> str:
    if not isinstance(spec, str) or not spec.strip():
        raise ValueError("Operation spec must be a non-empty string.")
    head = spec.strip().split("|", 1)[0].strip().lower()
    if re.match(r"^transf(?:or|ro)?m", head):
        return "transform"
    if head.startswith("crop"):
        return "crop"
    raise ValueError(f"Unknown operation type in spec header: '{head}'.")


def _is_Rt_spec(spec: str) -> bool:
    if not isinstance(spec, str):
        return False
    return bool(re.search(r"R\s*=\s*\[\[.*?\]\].*t\s*=\s*\[.*?\]", spec, flags=re.I | re.S))


def process_tiff_spec(src_path: str, dst_path: str, spec: str,
                      default_he_bins: int = 256, default_clahe_clip: float = 0.01) -> Dict[str, Any]:
    if _is_Rt_spec(spec):
        return apply_transform_to_image_file(src_path, dst_path, spec)

    op = _which_op(spec)

    if op == "transform":
        res = transform_tiff16_to_tiff8(
            src_path=src_path,
            dst_path=dst_path,
            transform_spec=spec,
            default_he_bins=default_he_bins,
            default_clahe_clip=default_clahe_clip,
        )
        res["operation"] = "transform"
        return res

    if op == "crop":
        res = crop_tiff_by_spec(src_path=src_path, dst_path=dst_path, crop_spec=spec)
        res["operation"] = "crop"
        return res

    raise ValueError(f"Unsupported operation: {op}")


def transform_tiff16_to_tiff8(src_path: str, dst_path: str, transform_spec: str,
                              default_he_bins: int = 256, default_clahe_clip: float = 0.01) -> Dict[str, Any]:
    """
    Transform conforme viewer.

    IMPORTANT:
    - Si spec contient Min(%) / Max(%), on recalcule lv/hv I16 sur l'image source (à chaque fois).
    """
    cfg = _parse_transform_spec(transform_spec)
    mode = cfg["mode"]

    # Charge image source
    arr = tiff.imread(src_path)
    if arr.ndim == 3:
        arr = arr[..., 0]
    if arr.dtype != np.uint16:
        arr = arr.astype(np.uint16, copy=False)
    arr16 = np.ascontiguousarray(arr)
    h, w = arr16.shape

    # Min/Max I16 effectifs
    if cfg.get("is_relative"):
        lv, hv = compute_low_high_from_percentiles(arr16, int(cfg["low_p"]), int(cfg["high_p"]))
    else:
        lv, hv = int(cfg["low_val"]), int(cfg["high_val"])

    he_bins = cfg["he_bins"] if cfg["he_bins"] is not None else int(default_he_bins)
    clahe_clip = cfg["clahe_clip"] if cfg["clahe_clip"] is not None else float(default_clahe_clip)

    rng = float(max(1, hv - lv))
    t = (arr16.astype(np.int32) - lv) / rng
    t = np.clip(t, 0.0, 1.0).astype(np.float32)

    # Applique mode
    if mode == "he":
        y = he_on_unit_float(t, nbins=int(he_bins))
        out = np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)

    elif mode == "clahe":
        y = clahe_on_unit_float(t, clip_limit=float(clahe_clip), nbins=int(he_bins))
        out = np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)

    elif mode == "wallis":
        mu_t = cfg.get("wallis_mu") if cfg.get("wallis_mu") is not None else 127.0
        sigma_t = cfg.get("wallis_sigma") if cfg.get("wallis_sigma") is not None else 35.0
        win_sz = cfg.get("wallis_win") if cfg.get("wallis_win") is not None else 15
        y = wallis_filter(t, win_size=int(win_sz), mu_target=float(mu_t), sigma_target=float(sigma_t))
        out = np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)

    elif mode == "canny":
        if not HAS_SKIMAGE:
            raise RuntimeError("Mode Canny demandé, mais scikit-image est indisponible.")
        sigma = cfg.get("canny_sigma") if cfg.get("canny_sigma") is not None else 1.2
        low = cfg.get("canny_low") if cfg.get("canny_low") is not None else 0.08
        high = cfg.get("canny_high") if cfg.get("canny_high") is not None else 0.20
        if high < low:
            high = low
        edges = sk_feature.canny(
            t,
            sigma=float(sigma),
            low_threshold=float(low),
            high_threshold=float(high),
        )
        out = (edges.astype(np.uint8) * 255)

    else:
        # modes pointwise (linear/gamma/...)
        y = Tiff16Viewer.apply_curve_pointwise(t, mode)
        out = np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)

    # Écrit TIFF 8-bit mono
    tiff.imwrite(dst_path, out, dtype=np.uint8, photometric='minisblack')

    # ✅ Return sans float(None)
    return {
        "src": src_path,
        "dst": dst_path,
        "height": int(h),
        "width": int(w),
        "mode": mode,

        "minmax_relative": bool(cfg.get("is_relative")),
        "low_p": _safe_int(cfg.get("low_p")) if cfg.get("is_relative") else None,
        "high_p": _safe_int(cfg.get("high_p")) if cfg.get("is_relative") else None,

        "low_val": int(lv),
        "high_val": int(hv),

        "he_bins": int(he_bins) if mode in ("he", "clahe") else None,
        "clahe_clip": float(clahe_clip) if mode == "clahe" else None,

        "wallis_mu": _safe_float(cfg.get("wallis_mu")) if mode == "wallis" else None,
        "wallis_sigma": _safe_float(cfg.get("wallis_sigma")) if mode == "wallis" else None,
        "wallis_win": _safe_int(cfg.get("wallis_win")) if mode == "wallis" else None,

        "canny_sigma": _safe_float(cfg.get("canny_sigma")) if mode == "canny" else None,
        "canny_low": _safe_float(cfg.get("canny_low")) if mode == "canny" else None,
        "canny_high": _safe_float(cfg.get("canny_high")) if mode == "canny" else None,
    }


# -------------------------------
# Batch helpers
# -------------------------------
def batch_process_tiff_folder(
    input_dir: str,
    output_dir: str,
    spec: str,
    default_he_bins: int = 256,
    default_clahe_clip: float = 0.01,
) -> Dict[str, Any]:
    if not os.path.isdir(input_dir):
        raise ValueError(f"Input directory does not exist or is not a directory: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    exts = {".tif", ".tiff"}
    names = sorted(
        [n for n in os.listdir(input_dir) if os.path.splitext(n)[1].lower() in exts],
        key=lambda s: s.lower()
    )

    results: List[Dict[str, Any]] = []
    processed = 0
    failed = 0

    for idx, name in enumerate(names):
        src = os.path.join(input_dir, name)
        dst = os.path.join(output_dir, name)
        print("process", idx + 1, "/", len(names))
        try:
            info = process_tiff_spec(
                src_path=src,
                dst_path=dst,
                spec=spec,
                default_he_bins=default_he_bins,
                default_clahe_clip=default_clahe_clip,
            )
            info.update({"src": src, "dst": dst, "ok": True})
            results.append(info)
            processed += 1
        except Exception as e:
            print(str(e))
            results.append({"src": src, "dst": dst, "ok": False, "error": str(e)})
            failed += 1

    return {
        "input_dir": os.path.abspath(input_dir),
        "output_dir": os.path.abspath(output_dir),
        "spec": spec,
        "total": len(names),
        "processed": processed,
        "failed": failed,
        "results": results,
    }


def batch_process_tiff_files(
    input_files: List[str],
    output_files: List[str],
    spec: List[str],
    progress_callback=None,
    argself=None
) -> Dict[str, Any]:
    default_he_bins = 256
    default_clahe_clip = 0.01

    if len(input_files) != len(output_files):
        raise ValueError("input_files and output_files must have the same length.")

    results: List[Dict[str, Any]] = []
    processed = 0
    failed = 0

    total = len(input_files)
    for idx, (src, dst) in enumerate(zip(input_files, output_files), start=0):
        print(f"process {idx + 1}/{total}")

        if progress_callback is not None:
            progress_value = float(100 * (idx + 1) / total)
            progress_callback(progress_value)

        if argself is not None and getattr(argself, "stop", False):
            break

        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        if os.path.exists(dst):
            os.remove(dst)

        try:
            info = process_tiff_spec(
                src_path=src,
                dst_path=dst,
                spec=spec[idx],
                default_he_bins=default_he_bins,
                default_clahe_clip=default_clahe_clip,
            )
            if isinstance(info, str):
                results.append({"src": src, "dst": dst, "ok": True})
            else:
                info.update({"src": src, "dst": dst, "ok": True})
                results.append(info)
            processed += 1
        except Exception as e:
            print("error batch_process_tiff_files", e)
            results.append({"src": src, "dst": dst, "ok": False, "error": str(e)})
            failed += 1

    return {
        "spec": spec,
        "total": total,
        "processed": processed,
        "failed": failed,
        "results": results,
    }


# ------------------
# Exemples:
#
# Viewer:
# w = view_tiff_qt("C:/img.tif")
# print(w.get_last_transform_spec())
#
# Transform (I16):
# spec = "Transform | Min (I16) = 1000 | Max (I16) = 60000 | Mode = Lineaire"
# transform_tiff16_to_tiff8("in.tif", "out.tif", spec)
#
# Transform (Relative % -> recalcule lv/hv pour chaque image):
# spec = "Transform | Min(%) = 2 | Max(%) = 98 | Mode = Canny (edges) | Canny sigma=1.2 | low=0.08 | high=0.20"
# transform_tiff16_to_tiff8("in.tif", "edges.tif", spec)
# batch_process_tiff_folder("C:/in_folder", "C:/out_folder", spec)
#
