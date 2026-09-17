# paper/make_panels.py
"""
Compose multi-panel figures from the single-panel PNGs already used in the manuscript
(cuts batch, group B). Pixels are tiled, not re-plotted, so each panel is exactly the
figure it replaces; only a panel label strip is added above each tile.

    fig_conformal_panels.png   (a) IMS  (b) XJTU-SY  (c) FEMTO  (d) ONGC      -- 2 x 2
    fig_tradeoff_panels.png    (a) IMS  (b) XJTU-SY                          -- 1 x 2

Run from the repository root:  python paper/make_panels.py
"""
import os

import matplotlib
from PIL import Image, ImageDraw, ImageFont

FILES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")
FONT = os.path.join(matplotlib.get_data_path(), "fonts", "ttf", "DejaVuSans-Bold.ttf")
STRIP = 44          # px label strip above each panel (panels are 150 dpi)
PAD = 12            # px gutter between panels


def compose(tiles, ncols, out):
    ims = [Image.open(os.path.join(FILES, f)).convert("RGBA") for f, _ in tiles]
    w = max(i.width for i in ims)
    h = max(i.height for i in ims) + STRIP
    nrows = (len(ims) + ncols - 1) // ncols
    canvas = Image.new("RGBA", (ncols * w + (ncols - 1) * PAD, nrows * h + (nrows - 1) * PAD),
                       (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT, 30)
    for k, (im, (_, label)) in enumerate(zip(ims, tiles)):
        r, c = divmod(k, ncols)
        x, y = c * (w + PAD), r * (h + PAD)
        draw.text((x + 8, y + 6), label, fill=(0, 0, 0, 255), font=font)
        canvas.paste(im, (x, y + STRIP), im)
    canvas.save(os.path.join(FILES, out), dpi=(150, 150))
    print("wrote", out, canvas.size)


if __name__ == "__main__":
    compose([("fig_conf_ims.png", "(a) IMS"), ("fig_conf_xjtu.png", "(b) XJTU-SY"),
             ("fig_conf_femto.png", "(c) FEMTO/PRONOSTIA"), ("fig_conf_ongc.png", "(d) ONGC")],
            2, "fig_conformal_panels.png")
    compose([("fig_tradeoff_ims.png", "(a) IMS"), ("fig_tradeoff_xjtu.png", "(b) XJTU-SY")],
            2, "fig_tradeoff_panels.png")
