"""Deterministic broadsheet newspaper front page generator."""

import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1024
HEIGHT = 1024
BG_PAPER = "#f7f2e7"
INK_DARK = "#1a1d24"
INK_MUTED = "#4e545f"
NAVY_BAND = "#132238"
RED_ACCENT = "#b8292f"
RULE_COLOR = "#252932"
SCENE_BORDER = "#cfc7b4"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

STATS_BAR = (
    "110+ missiles & 400 drones fired at Ukraine • "
    "372,000 evacuated from Cyclone Akvan • "
    "10,000 Rohingya in Malaysia's resettlement plan • "
    "100,000 youth visas a year in the EU–UK deal"
)
FOOTER_LEFT = (
    "ODISHA: Cyclone Akvan ends with no deaths reported; "
    "372,000 evacuated, Patrapur took 209 mm of rain."
)
FOOTER_RIGHT = (
    "BAGHDAD: Iraq opens a security HQ in Jurf al-Sakhar on Saturday "
    "to oversee Kataib Hezbollah's withdrawal."
)


def load_font(filename: str, size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    """Load a TrueType font from FONT_DIR, falling back to DejaVuSans or default."""
    for candidate in (FONT_DIR / filename, FONT_DIR / "DejaVuSans.ttf"):
        if candidate.is_file():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def measure_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
) -> tuple[int, int]:
    """Return (width, height) of rendered text using textbbox."""
    if not text:
        return (0, 0)
    bbox = draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Greedily wrap text into lines that fit within max_width."""
    words = text.split()
    if not words:
        return []

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        w, _ = measure_text(draw, candidate, font)
        if w <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_file: str,
    max_width: int,
    max_height: int,
    max_lines: int,
    start_size: int,
    min_size: int = 7,
    line_spacing_ratio: float = 1.22,
) -> tuple[ImageFont.ImageFont | ImageFont.FreeTypeFont, list[str], int]:
    """Find the largest font size that fits text within the given box."""
    best_font = load_font(font_file, min_size)
    best_lines = wrap_text(draw, text, best_font, max_width)[:max_lines]
    best_line_h = max(1, round(min_size * line_spacing_ratio))

    for size in range(start_size, min_size - 1, -1):
        font = load_font(font_file, size)
        lines = wrap_text(draw, text, font, max_width)
        line_h = max(1, round(size * line_spacing_ratio))
        if len(lines) <= max_lines and len(lines) * line_h <= max_height:
            return (font, lines, line_h)

    return (best_font, best_lines, best_line_h)


def draw_text_lines(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    lines: Iterable[str],
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    line_h: int,
    fill: str,
) -> None:
    """Draw multiple lines of text starting at (x, y) spaced by line_h."""
    for idx, line in enumerate(lines):
        draw.text((x, y + idx * line_h), line, font=font, fill=fill)


def draw_star(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    outer_r: float,
    inner_r: float,
    fill: str,
    points: int = 5,
) -> None:
    """Draw a filled polygon star centered at (cx, cy)."""
    coords: list[tuple[float, float]] = []
    step = math.pi / points
    start_angle = -math.pi / 2
    for i in range(points * 2):
        radius = outer_r if i % 2 == 0 else inner_r
        angle = start_angle + i * step
        coords.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    draw.polygon(coords, fill=fill)


def _draw_angled_missile(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    length: float,
    half_w: float,
    angle_rad: float,
    fill: str,
) -> None:
    """Draw a slim elongated missile body with tail fins angled nose-down."""
    ca, sa = math.cos(angle_rad), math.sin(angle_rad)
    px, py = -sa, ca
    nose = (cx + ca * length * 0.55, cy + sa * length * 0.55)
    body_f = (cx + ca * length * 0.25, cy + sa * length * 0.25)
    tail = (cx - ca * length * 0.45, cy - sa * length * 0.45)

    body = [
        nose,
        (body_f[0] + px * half_w, body_f[1] + py * half_w),
        (tail[0] + px * half_w, tail[1] + py * half_w),
        (tail[0] - px * half_w, tail[1] - py * half_w),
        (body_f[0] - px * half_w, body_f[1] - py * half_w),
    ]
    draw.polygon(body, fill=fill)

    fin_span = half_w * 2.6
    fin_len = length * 0.18
    fin_front = (tail[0] + ca * fin_len, tail[1] + sa * fin_len)
    draw.polygon(
        [
            fin_front,
            (tail[0] + px * fin_span, tail[1] + py * fin_span),
            (tail[0] - px * fin_span, tail[1] - py * fin_span),
        ],
        fill=fill,
    )


def scene_warsaw_nato(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    """Render falling missiles/drone and NATO badge inside box."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill="#dfe7ee", outline=SCENE_BORDER, width=1)
    draw.rectangle([x0 + 1, y1 - 12, x1 - 1, y1 - 1], fill="#5c6650")

    smoke_color = "#b7c1cc"
    # Smoke trails (curved polylines)
    draw.line(
        [(x0 + 36, y0 + 14), (x0 + 54, y0 + 24), (x0 + 70, y0 + 30), (x0 + 86, y0 + 40)],
        fill=smoke_color,
        width=2,
    )
    draw.line(
        [(x0 + 148, y0 + 10), (x0 + 164, y0 + 18), (x0 + 178, y0 + 27), (x0 + 190, y0 + 34)],
        fill=smoke_color,
        width=2,
    )
    draw.line(
        [(x0 + 252, y0 + 10), (x0 + 266, y0 + 18), (x0 + 280, y0 + 24), (x0 + 292, y0 + 32)],
        fill=smoke_color,
        width=2,
    )

    # Upper-left cruise missile (larger)
    _draw_angled_missile(draw, x0 + 102, y0 + 48, length=34, half_w=2.6, angle_rad=0.58, fill="#3a4352")
    # Upper-center second smaller missile
    _draw_angled_missile(draw, x0 + 202, y0 + 41, length=24, half_w=2.0, angle_rad=0.62, fill="#3a4352")
    # Upper-right jet drone (delta-wing silhouette)
    dx, dy = x0 + 304, y0 + 36
    draw.polygon(
        [
            (dx + 14, dy + 8),
            (dx - 10, dy + 6),
            (dx - 5, dy - 1),
            (dx - 11, dy - 10),
        ],
        fill="#3a4352",
    )

    # Right-center NATO badge
    cx, cy, r = x1 - 66, y0 + 44, 30
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#1a3668")
    draw_star(draw, cx, cy, outer_r=20, inner_r=6, fill="#ffffff", points=4)


def scene_climate_cop31(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    """Render sun, globe, and factory silhouette inside box."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill="#e6ece6", outline=SCENE_BORDER, width=1)

    # Sun top-right
    sx, sy, sr = x1 - 46, y0 + 25, 14
    for i in range(8):
        ang = i * (math.pi / 4)
        rx0 = sx + (sr + 3) * math.cos(ang)
        ry0 = sy + (sr + 3) * math.sin(ang)
        rx1 = sx + (sr + 9) * math.cos(ang)
        ry1 = sy + (sr + 9) * math.sin(ang)
        draw.line([(rx0, ry0), (rx1, ry1)], fill="#d9822b", width=2)
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill="#e89c31")

    # Globe center-left
    gx, gy, gr = x0 + 116, y0 + 48, 35
    draw.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill="#4b89a8", outline="#2b556b", width=2)
    # Two green continent polygons
    draw.polygon(
        [
            (gx - 22, gy - 16),
            (gx - 6, gy - 22),
            (gx + 2, gy - 8),
            (gx - 8, gy + 4),
            (gx - 20, gy - 2),
        ],
        fill="#72a163",
    )
    draw.polygon(
        [
            (gx + 8, gy - 4),
            (gx + 24, gy - 10),
            (gx + 26, gy + 12),
            (gx + 12, gy + 20),
            (gx + 4, gy + 8),
        ],
        fill="#72a163",
    )
    # One latitude arc
    draw.arc([gx - 33, gy - 10, gx + 33, gy + 16], start=12, end=168, fill="#2b556b", width=1)

    # Factory silhouette bottom-right
    fx0, fx1, fy_bot = x1 - 156, x1 - 36, y1 - 2
    # Two smokestacks
    draw.rectangle([fx0 + 14, fy_bot - 52, fx0 + 24, fy_bot - 22], fill="#2d333b")
    draw.rectangle([fx0 + 36, fy_bot - 44, fx0 + 46, fy_bot - 22], fill="#2d333b")
    # Sawtooth roof body
    draw.polygon(
        [
            (fx0, fy_bot),
            (fx0, fy_bot - 26),
            (fx0 + 30, fy_bot - 38),
            (fx0 + 30, fy_bot - 26),
            (fx0 + 60, fy_bot - 38),
            (fx0 + 60, fy_bot - 26),
            (fx0 + 90, fy_bot - 38),
            (fx0 + 90, fy_bot - 26),
            (fx1, fy_bot - 38),
            (fx1, fy_bot),
        ],
        fill="#2d333b",
    )
    # Three gray smoke puffs
    for px, py, pr in (
        (fx0 + 25, fy_bot - 62, 6),
        (fx0 + 40, fy_bot - 70, 8),
        (fx0 + 58, fy_bot - 76, 10),
    ):
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill="#9aa3ad")


def scene_berlin_europe(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    """Render brick wall on left half and EU-style badge on right half."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill="#ebe4d6", outline=SCENE_BORDER, width=1)

    # Brick wall on left half: 5 rows x 5 cols of 28x12 bricks with 2px gaps
    wall_x0 = x0 + 40
    wall_y0 = y0 + 12
    brick_w, brick_h, gap = 28, 12, 2
    for row in range(5):
        for col in range(5):
            bx0 = wall_x0 + col * (brick_w + gap)
            by0 = wall_y0 + row * (brick_h + gap)
            color = "#b4533c" if (row + col) % 2 == 0 else "#9e432e"
            draw.rectangle(
                [bx0, by0, bx0 + brick_w, by0 + brick_h],
                fill=color,
                outline="#e8dfd0",
                width=1,
            )
    wall_w = 5 * brick_w + 4 * gap
    wall_h = 5 * brick_h + 4 * gap
    draw.rectangle(
        [wall_x0 - 3, wall_y0 + wall_h + 2, wall_x0 + wall_w + 3, wall_y0 + wall_h + 7],
        fill="#7d7668",
    )

    # Navy badge circle on right half with 12 gold stars
    cx, cy, r = x0 + 344, y0 + 48, 36
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#1a3668")
    ring_r = 25
    for i in range(12):
        ang = -math.pi / 2 + i * (2 * math.pi / 12)
        sx = cx + ring_r * math.cos(ang)
        sy = cy + ring_r * math.sin(ang)
        draw_star(draw, sx, sy, outer_r=4.2, inner_r=1.8, fill="#f2c94c", points=5)


def scene_markets_fall(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    """Render descending market bars, downward arrow, and chip icon inside box."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill="#e6eaef", outline=SCENE_BORDER, width=1)

    # Three subtle horizontal grid lines
    for gy in (y0 + 24, y0 + 44, y0 + 64):
        draw.line([(x0 + 18, gy), (x1 - 18, gy)], fill="#d0d7e0", width=1)

    # Baseline near the bottom
    base_y = y1 - 12
    draw.line([(x0 + 54, base_y), (x1 - 54, base_y)], fill="#3a4352", width=2)

    # Five descending bars centered
    heights = (62, 50, 40, 30, 20)
    colors = ("#8a2b2e", "#a02c30", "#b8292f", "#c23a3a", "#cf4a45")
    bar_w, gap = 36, 18
    total_w = len(heights) * bar_w + (len(heights) - 1) * gap
    start_x = (x0 + x1 - total_w) // 2

    for i, (h, color) in enumerate(zip(heights, colors)):
        bx0 = start_x + i * (bar_w + gap)
        draw.rectangle([bx0, base_y - h, bx0 + bar_w, base_y - 1], fill=color)

    # Downward arrow polyline from top-left of first bar to below last bar
    ax0, ay0 = start_x - 6, base_y - heights[0] - 4
    ax1, ay1 = start_x + total_w + 10, base_y - 6
    mid_x = (ax0 + ax1) / 2
    mid_y = (ay0 + ay1) / 2 - 4
    draw.line([(ax0, ay0), (mid_x, mid_y), (ax1, ay1)], fill=RED_ACCENT, width=4)
    # Small arrowhead polygon
    ang = math.atan2(ay1 - mid_y, ax1 - mid_x)
    head_len = 10
    draw.polygon(
        [
            (ax1 + 3 * math.cos(ang), ay1 + 3 * math.sin(ang)),
            (ax1 - head_len * math.cos(ang - 0.5), ay1 - head_len * math.sin(ang - 0.5)),
            (ax1 - head_len * math.cos(ang + 0.5), ay1 - head_len * math.sin(ang + 0.5)),
        ],
        fill=RED_ACCENT,
    )

    # Small dark chip rectangle in top-right corner with tiny gold contact dots
    cx0, cy0, cx1, cy1 = x1 - 48, y0 + 10, x1 - 16, y0 + 28
    draw.rectangle([cx0, cy0, cx1, cy1], fill="#2d333b")
    for dx in range(cx0 + 5, cx1 - 3, 6):
        draw.ellipse([dx - 1, cy0 + 4, dx + 1, cy0 + 6], fill="#f2c94c")
        draw.ellipse([dx - 1, cy1 - 6, dx + 1, cy1 - 4], fill="#f2c94c")


def scene_rohingya(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    """Render shore houses, map pin, sea waves, and wooden boat inside box."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill="#e8ece7", outline=SCENE_BORDER, width=1)

    # Sea at the bottom third
    sea_top = y1 - 32
    draw.rectangle([x0 + 1, sea_top, x1 - 1, y1 - 1], fill="#3b6e8c")
    # Layered wave arcs in #3b6e8c and white
    for wx in range(x0 + 110, x1 - 24, 34):
        draw.arc([wx, sea_top - 5, wx + 32, sea_top + 9], start=180, end=360, fill="#3b6e8c", width=2)
        draw.arc([wx + 6, sea_top + 8, wx + 32, sea_top + 18], start=0, end=180, fill="#ffffff", width=2)
        draw.arc([wx - 6, sea_top + 18, wx + 20, sea_top + 28], start=0, end=180, fill="#ffffff", width=1)

    # Shore at left with two small houses
    draw.polygon(
        [(x0 + 1, sea_top - 4), (x0 + 126, sea_top - 4), (x0 + 148, y1 - 1), (x0 + 1, y1 - 1)],
        fill="#b8ae93",
    )
    houses = [
        (x0 + 28, sea_top - 22, "#8ca077", "#b4533c"),
        (x0 + 68, sea_top - 20, "#8ca077", "#b4533c"),
    ]
    for hx, hy, wall_c, roof_c in houses:
        draw.rectangle([hx, hy, hx + 22, hy + 18], fill=wall_c)
        draw.polygon([(hx - 3, hy), (hx + 11, hy - 12), (hx + 25, hy)], fill=roof_c)

    # Map pin above first house
    px, py = x0 + 39, sea_top - 48
    draw.polygon([(px - 5, py + 4), (px + 5, py + 4), (px, py + 14)], fill=RED_ACCENT)
    draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=RED_ACCENT)
    draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill="#ffffff")

    # Wooden boat on the sea
    bx, by = x0 + 290, sea_top + 6
    # Three seated figure silhouettes
    for fx in (bx - 22, bx, bx + 20):
        draw.ellipse([fx - 4, by - 16, fx + 4, by - 8], fill="#2d333b")
        draw.polygon([(fx - 6, by), (fx - 4, by - 8), (fx + 4, by - 8), (fx + 6, by)], fill="#2d333b")
    # Mast & triangular sail
    draw.line([(bx + 4, by), (bx + 4, by - 46)], fill="#5c3d24", width=2)
    draw.polygon([(bx + 6, by - 44), (bx + 6, by - 8), (bx + 36, by - 10)], fill="#e8dfd0")
    # Hull polygon
    draw.polygon(
        [(bx - 42, by), (bx + 44, by), (bx + 30, by + 13), (bx - 30, by + 13)],
        fill="#7a5230",
    )


def scene_cricket(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    """Render cricket pitch, stumps, bat, ball, and sun inside box."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill="#e9efe4", outline=SCENE_BORDER, width=1)

    # Small sun in top-left corner
    sx, sy, sr = x0 + 34, y0 + 24, 10
    for i in range(8):
        ang = i * (math.pi / 4)
        draw.line(
            [
                (sx + (sr + 2) * math.cos(ang), sy + (sr + 2) * math.sin(ang)),
                (sx + (sr + 6) * math.cos(ang), sy + (sr + 6) * math.sin(ang)),
            ],
            fill="#d9822b",
            width=2,
        )
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill="#e89c31")

    # Pitch strip in center
    cx = (x0 + x1) // 2
    draw.rectangle([cx - 34, y0 + 6, cx + 34, y1 - 6], fill="#d9c9a3")

    # Three stumps with two bails at pitch's lower end
    stump_bot = y1 - 12
    stump_top = stump_bot - 30
    for sx_off in (-10, 0, 10):
        draw.rectangle([cx + sx_off - 1, stump_top, cx + sx_off + 2, stump_bot], fill="#c9a227")
    draw.rectangle([cx - 10, stump_top - 2, cx - 1, stump_top], fill="#a68117")
    draw.rectangle([cx + 1, stump_top - 2, cx + 10, stump_top], fill="#a68117")

    # Leaning cricket bat beside stumps
    bat_x, bat_y = cx + 44, y1 - 14
    draw.line([(bat_x + 12, bat_y - 34), (bat_x + 20, bat_y - 54)], fill="#4b3621", width=4)
    draw.rounded_rectangle(
        [bat_x - 2, bat_y - 36, bat_x + 14, bat_y],
        radius=3,
        fill="#b98a4a",
        outline="#8a6230",
        width=1,
    )

    # Red ball mid-flight with white seam arc and motion dashes
    ball_x, ball_y, br = cx + 96, y0 + 34, 9
    for d in range(3):
        dx = ball_x - 20 - d * 12
        dy = ball_y - 4 - d * 3
        draw.line([(dx - 6, dy - 1), (dx, dy + 1)], fill="#8f98a3", width=2)
    draw.ellipse([ball_x - br, ball_y - br, ball_x + br, ball_y + br], fill="#b8292f")
    draw.arc([ball_x - 6, ball_y - 6, ball_x + 6, ball_y + 6], start=35, end=145, fill="#ffffff", width=1)


PANELS = [
    (
        "01",
        "EUROPE • WARSAW",
        "NATO Chief Heads to Warsaw After Russian Weapons Fell in Poland",
        "A Kh-101 cruise missile, a second missile and a jet drone came down in southeast Poland with no casualties; Warsaw calls it a deliberate provocation and seeks more NATO troops.",
        scene_warsaw_nato,
    ),
    (
        "02",
        "CLIMATE • COP31 ANTALYA",
        "COP31 Slips Into Overtime With Fossil Fuels Scrubbed From Draft",
        "The summit ran past Friday's close with no deal; a third draft is due Saturday after all fossil-fuel language was removed from the text.",
        scene_climate_cop31,
    ),
    (
        "03",
        "EUROPE • BRUSSELS",
        "UK and EU Seal Reset Package in Brussels",
        "Food checks scrapped, emissions trading linked and 100,000 youth visas a year agreed in Friday's reset; student fee talks are deferred six months.",
        scene_berlin_europe,
    ),
    (
        "04",
        "MARKETS • NVIDIA",
        "Nvidia Falls 14% as SEC Reviews Its Accounting",
        "Reuters reveals an SEC enforcement review of the chipmaker's bookkeeping; California's attorney general has also issued a subpoena. Seventh straight loss.",
        scene_markets_fall,
    ),
    (
        "05",
        "ASIA • KUALA LUMPUR",
        "Malaysia to Resettle 10,000 Rohingya in Türkiye",
        "A structured skills-training scheme would move 10,000 refugees in one of the largest Rohingya resettlements since 2017. Türkiye has yet to confirm in public.",
        scene_rohingya,
    ),
    (
        "06",
        "SPORT • WELLINGTON",
        "Rahul Nears Century as India Close In at Wellington",
        "KL Rahul reaches 93 not out as India make 239-1 by lunch on day three, cutting New Zealand's first-innings lead to 129 runs.",
        scene_cricket,
    ),
]


def render_front_page(out_path: str | Path) -> Path:
    """Render the broadsheet front page header and verified-stats bar to a PNG."""
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_PAPER)
    draw = ImageDraw.Draw(img)

    content_left = 32
    content_right = 992
    content_width = content_right - content_left

    # Top double rule
    draw.line([(content_left, 24), (content_right, 24)], fill=RULE_COLOR, width=2)
    draw.line([(content_left, 28), (content_right, 28)], fill=RULE_COLOR, width=1)

    # Centered kicker
    kicker_text = "GLOBAL FRONT PAGE • SIX KEY STORIES • 24-HOUR SUMMARY"
    kicker_font = load_font("DejaVuSans-Bold.ttf", 11)
    kicker_w, _ = measure_text(draw, kicker_text, kicker_font)
    draw.text(((WIDTH - kicker_w) / 2, 35), kicker_text, font=kicker_font, fill=INK_MUTED)

    # Centered masthead
    masthead_text = "WORLD NEWS"
    masthead_font = load_font("DejaVuSerif-Bold.ttf", 62)
    masthead_w, _ = measure_text(draw, masthead_text, masthead_font)
    draw.text(((WIDTH - masthead_w) / 2, 50), masthead_text, font=masthead_font, fill=INK_DARK)

    # Navy band with 14px red end caps
    band_top = 122
    band_bottom = 152
    cap_width = 14
    draw.rectangle([content_left, band_top, content_right, band_bottom], fill=NAVY_BAND)
    draw.rectangle([content_left, band_top, content_left + cap_width, band_bottom], fill=RED_ACCENT)
    draw.rectangle([content_right - cap_width, band_top, content_right, band_bottom], fill=RED_ACCENT)

    date_text = "SATURDAY 21 NOVEMBER 2026"
    date_font = load_font("DejaVuSans-Bold.ttf", 14)
    draw.text(
        (WIDTH / 2, (band_top + band_bottom) / 2),
        date_text,
        font=date_font,
        fill="#ffffff",
        anchor="mm",
    )

    # Thin verified-stats bar
    stats_top = 159
    stats_bottom = 181
    draw.line([(content_left, stats_top), (content_right, stats_top)], fill=RULE_COLOR, width=1)
    draw.line([(content_left, stats_bottom), (content_right, stats_bottom)], fill=RULE_COLOR, width=1)

    stats_font = load_font("DejaVuSans-Bold.ttf", 7)
    for size in range(10, 6, -1):
        candidate_font = load_font("DejaVuSans-Bold.ttf", size)
        text_w, _ = measure_text(draw, STATS_BAR, candidate_font)
        if text_w <= content_width:
            stats_font = candidate_font
            break

    draw.text(
        (WIDTH / 2, (stats_top + stats_bottom) / 2),
        STATS_BAR,
        font=stats_font,
        fill=INK_DARK,
        anchor="mm",
    )

    # Story panel grid (2 columns x 3 rows)
    margin = 32
    col_w = 468
    col_gap = 24
    row_h = 248
    row_gap = 14
    grid_top = 186
    tag_font = load_font("DejaVuSans-Bold.ttf", 11)

    for idx, (num, tag, headline, sub, scene_fn) in enumerate(PANELS):
        col = idx % 2
        row = idx // 2
        px = margin + col * (col_w + col_gap)
        py = grid_top + row * (row_h + row_gap)
        row_bottom = py + row_h

        draw.line([(px, py), (px + col_w, py)], fill=RULE_COLOR, width=2)

        draw.text((px, py + 6), tag, font=tag_font, fill=RED_ACCENT)
        num_w, _ = measure_text(draw, num, tag_font)
        draw.text((px + col_w - num_w, py + 6), num, font=tag_font, fill=INK_MUTED)

        scene_fn(draw, (px, py + 26, px + col_w, py + 122))

        h_font, h_lines, h_line_h = fit_text_block(
            draw,
            headline,
            "DejaVuSerif-Bold.ttf",
            max_width=col_w,
            max_height=50,
            max_lines=2,
            start_size=19,
            min_size=12,
        )
        headline_y = py + 130
        draw_text_lines(draw, px, headline_y, h_lines, h_font, h_line_h, INK_DARK)

        sub_y = headline_y + len(h_lines) * h_line_h + 5
        sub_max_h = max(1, row_bottom - sub_y)
        s_font, s_lines, s_line_h = fit_text_block(
            draw,
            sub,
            "DejaVuSans.ttf",
            max_width=col_w,
            max_height=sub_max_h,
            max_lines=3,
            start_size=13,
            min_size=9,
            line_spacing_ratio=1.24,
        )
        draw_text_lines(draw, px, sub_y, s_lines, s_font, s_line_h, INK_MUTED)

    # Footer rule and two strips
    draw.line([(content_left, 958), (content_right, 958)], fill=RULE_COLOR, width=1)
    footer_y = 970
    footer_h = 26
    footer_max_w = col_w - 18

    footer_font = load_font("DejaVuSans-Bold.ttf", 7)
    for size in range(11, 6, -1):
        candidate_font = load_font("DejaVuSans-Bold.ttf", size)
        w_left, _ = measure_text(draw, FOOTER_LEFT, candidate_font)
        w_right, _ = measure_text(draw, FOOTER_RIGHT, candidate_font)
        if w_left <= footer_max_w and w_right <= footer_max_w:
            footer_font = candidate_font
            break

    footer_items = (
        (margin, RED_ACCENT, FOOTER_LEFT),
        (margin + col_w + col_gap, NAVY_BAND, FOOTER_RIGHT),
    )
    icon_y = footer_y + (footer_h - 12) // 2
    text_cy = footer_y + footer_h / 2
    for fx, icon_color, footer_text in footer_items:
        draw.rectangle([fx, icon_y, fx + 12, icon_y + 12], fill=icon_color)
        draw.text((fx + 18, text_cy), footer_text, font=footer_font, fill=INK_DARK, anchor="lm")

    img.save(out_file, format="PNG", optimize=True)
    return out_file


def main() -> None:
    """Render entry.png in the same directory as this script."""
    render_front_page(Path(__file__).resolve().parent / "entry.png")


if __name__ == "__main__":
    main()
