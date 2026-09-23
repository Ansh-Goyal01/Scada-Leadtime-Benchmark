"""One font and one set of detector names for all six manuscript figures.

Font: STIX for text AND mathtext. Computer Modern ("mathtext.fontset": "cm") uses the
BaKoMa fonts, whose TeX-specific internal encoding puts sigma at the code point of "3/4"
and alpha at "(R)": even embedded as Type 42 the PDF text layer then reads "3¾" and
"Target FAR (®)". STIX is Unicode-mapped, Times-like (matching the body text) and ships
with matplotlib. pdf.fonttype 42 embeds TrueType instead of Type 3.

Detector names: the table names (Tables 2, 5, 6), keyed by short_name so no script can
drift ("IsoForest", "Iso. Forest", "IF"; "LSTM-Autoencoder"; "3sigma Rule (sigma=3.0)").
"""
import matplotlib.pyplot as plt

RC = {"font.family": "STIXGeneral", "mathtext.fontset": "stix", "pdf.fonttype": 42,
      "ps.fonttype": 42, "axes.unicode_minus": True}

LABELS = {"three_sigma": r"$3\sigma$", "ewma": "EWMA", "cusum": "CUSUM",
          "hotelling_t2": r"Hotelling $T^2$", "isolation_forest": "Iso. Forest",
          "deep_svdd": "Deep SVDD", "one_class_svm": "One-class SVM", "lstm_ae": "LSTM-AE",
          "tcn": "TCN-AE", "transformer_ad": "Transformer-AD", "rms_trend": "RMS-trend"}

COLUMN_WIDTH_IN = 3.35   # \columnwidth of the two-column IJPHM template
TEXT_WIDTH_IN = 7.0      # \textwidth


def apply(size=7.0, **extra):
    """Set the shared style; extra rcParams (sizes, line widths) are layered on top."""
    plt.rcParams.update({**RC, "font.size": size, **extra})


def label(short_name):
    """Table name of a detector; an unknown short_name fails loudly."""
    return LABELS[short_name]
