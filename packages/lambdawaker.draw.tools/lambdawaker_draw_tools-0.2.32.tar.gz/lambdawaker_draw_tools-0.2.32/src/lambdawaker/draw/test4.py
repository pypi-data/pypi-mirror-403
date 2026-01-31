import random

import aggdraw
import numpy as np
from PIL import Image


# -----------------------------
# Helpers
# -----------------------------
def world_to_px_factory(width, height, xlim, ylim):
    """
    Creates a mapping function from "world" coords (your math space)
    into pixel coords (image space). Y is flipped because images grow down.
    """
    x0, x1 = xlim
    y0, y1 = ylim
    sx = (width - 1) / (x1 - x0)
    sy = (height - 1) / (y1 - y0)

    def w2p(x, y):
        px = (x - x0) * sx
        py = (y1 - y) * sy  # flip y-axis
        return px, py

    return w2p


def draw_polyline(draw, points, color, width_px=1, opacity=255):
    """
    Draws an antialiased polyline using aggdraw.
    points: iterable of (x, y) pixel coordinates (floats ok).
    """
    # aggdraw likes a flat sequence, but also accepts tuples list in many cases.
    # We'll flatten to be safe.
    flat = []
    for x, y in points:
        flat.extend([x, y])

    pen = aggdraw.Pen(color, width_px, opacity)
    draw.line(flat, pen)


# -----------------------------
# Ribbon generator
# -----------------------------
def add_ribbon(
        draw,
        w2p,
        x_range,
        math_func_a,
        math_func_b,
        base_y,
        amplitude=1.0,
        frequency=0.4,
        spread_factor=0.03,
        color="#A3C1E0",
        num_lines=80,
        samples=1000,
        line_width_px=2,
        xx=1,
        phase=0
):
    """
    Generates a single 'ribbon' artifact made of multiple micro-waves.
    Rendered as many thin polylines with varying opacity.
    """
    x = np.linspace(x_range[0], x_range[1], samples)

    # Master path for this specific ribbon
    master_flow = amplitude * np.sin(x * frequency) + base_y

    for i in range(num_lines):
        micro = 0.04 * math_func_b(x * 15 + (i * 0.2))
        spread = xx * np.abs(math_func_a((x + phase) * 0.2) * (i * spread_factor))

        y = master_flow + micro + spread

        # Faded edges for a professional look
        alpha_val = 0.1 + (0.2 * math_func_a(np.pi * i / num_lines))  # ~0.1..0.3
        opacity = int(np.clip(alpha_val, 0.0, 1.0) * 255)

        pts = [w2p(xj, yj) for xj, yj in zip(x, y)]

        draw_polyline(draw, pts, color=color, width_px=line_width_px, opacity=opacity)


def compose_document(
        out_path="id_background.png",
        width=2400,
        height=1600,
        dpi=None,  # unused by PIL, but left here if you want metadata later
):
    """
    Layers multiple artifacts to create the final background layout.
    Produces a PNG with a clean, borderless composition.
    """
    # World-space limits (match your matplotlib version)
    x_limit = (0, 25)
    y_limit = (0, 10)

    w2p = world_to_px_factory(width, height, x_limit, y_limit)

    # Background
    img = Image.new("RGBA", (width, height), "#FDFDFD")
    d = aggdraw.Draw(img)

    math_func_a = random.choice((np.tanh, np.sin, np.tan))
    math_func_b = random.choice((np.tanh, np.sin, np.tan))

    r_phase = random.random() * 360

    for i in range(5):
        add_ribbon(
            d, w2p, x_limit,
            math_func_a=math_func_a,
            math_func_b=math_func_b,
            base_y=0 + i * 2.3,
            amplitude=.1,
            frequency=.1,
            spread_factor=0.03,
            color="#B8D1EA",
            num_lines=80,
            samples=1000,
            line_width_px=1,
            phase=0 + i * 8 + r_phase,
        )

        add_ribbon(
            d, w2p, x_limit,
            math_func_a=math_func_a,
            math_func_b=math_func_b,
            base_y=2.3 + i * 2.3,
            amplitude=.1,
            frequency=.1,
            spread_factor=0.03,
            color="#B8D1EA",
            num_lines=80,
            samples=1000,
            line_width_px=1,
            xx=-1,
            phase=8 + i * 8 + r_phase
        )

    # --- LAYER 4: Deep Background 'Ghost' Waves ---
    for offset in range(3, 7, 2):
        x_ghost = np.linspace(x_limit[0], x_limit[1], 1000)
        y_ghost = 0.2 * np.sin(x_ghost * 0.1) + offset

        # Your matplotlib used linewidth=0.3 and alpha=0.2.
        # Here we approximate with a 1px line and low opacity.
        opacity = int(0.2 * 255)
        pts = [w2p(xj, yj) for xj, yj in zip(x_ghost, y_ghost)]
        draw_polyline(d, pts, color="#E1EBF5", width_px=1, opacity=opacity)

    # Finalize aggdraw rendering onto the PIL image
    d.flush()

    img.show()
    return img


if __name__ == "__main__":
    compose_document("id_background.png", width=800, height=600)
    print("Saved: id_background.png")
