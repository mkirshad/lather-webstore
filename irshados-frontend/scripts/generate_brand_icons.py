import math
import struct
import zlib
from pathlib import Path

BLUE = (0x25, 0x63, 0xEB, 0xFF)
INV_ALPHA = 1.0
CENTER_X = 580.0
CENTER_Y = 520.0
RADIUS = 340.0
STROKE_HALF = 95.0 / 2.0
RING_MIN = RADIUS - STROKE_HALF
RING_MAX = RADIUS + STROKE_HALF
GAP_MIN = -120.0
GAP_MAX = -60.0

PILLAR_LEFT = 177.0
PILLAR_RIGHT = 263.0
PILLAR_TOP = 239.5
PILLAR_BOTTOM = 800.5
PILLAR_RADIUS = 43.0

LINE_LEFT = 560.0
LINE_RIGHT = 600.0
LINE_TOP = 384.0
LINE_BOTTOM = 565.3


def draw_icon(size: int, output: Path) -> None:
    inv_scale = 1000.0 / size
    pixels = bytearray(size * size * 4)

    def set_pixel(x: int, y: int):
        idx = (y * size + x) * 4
        pixels[idx : idx + 4] = bytes(BLUE)

    for y in range(size):
        oy = (y + 0.5) * inv_scale
        for x in range(size):
            ox = (x + 0.5) * inv_scale

            # Determine whether this pixel belongs to any brand geometry.
            draw = False

            # Pillar with rounded corners.
            if PILLAR_LEFT <= ox <= PILLAR_RIGHT and PILLAR_TOP <= oy <= PILLAR_BOTTOM:
                # Check corner rounding by ensuring distance to the nearest corner is within radius.
                corner_x = PILLAR_LEFT if ox < (PILLAR_LEFT + PILLAR_RADIUS) else (
                    PILLAR_RIGHT if ox > (PILLAR_RIGHT - PILLAR_RADIUS) else None
                )
                corner_y = PILLAR_TOP if oy < (PILLAR_TOP + PILLAR_RADIUS) else (
                    PILLAR_BOTTOM if oy > (PILLAR_BOTTOM - PILLAR_RADIUS) else None
                )
                if corner_x is None or corner_y is None:
                    draw = True
                else:
                    dx = ox - corner_x
                    dy = oy - corner_y
                    if dx * dx + dy * dy <= PILLAR_RADIUS * PILLAR_RADIUS:
                        draw = True

            if not draw:
                # Power line block.
                if LINE_LEFT <= ox <= LINE_RIGHT and LINE_TOP <= oy <= LINE_BOTTOM:
                    draw = True

            if not draw:
                # Outer ring with top gap.
                dx = ox - CENTER_X
                dy = oy - CENTER_Y
                dist = math.hypot(dx, dy)
                if RING_MIN <= dist <= RING_MAX:
                    angle = math.degrees(math.atan2(dy, dx))
                    if not (GAP_MIN < angle < GAP_MAX):
                        draw = True

            if draw:
                set_pixel(x, y)

    # Encode PNG (RGBA, 8-bit per channel, non-interlaced)
    stride = size * 4
    raw_bytes = bytearray()
    for y in range(size):
        raw_bytes.append(0)  # no filter
        raw_bytes.extend(pixels[y * stride : (y + 1) * stride])

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png_data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw_bytes))) + chunk(b"IEND", b"")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(png_data)


def main() -> None:
    base = Path("public/img/logo")
    draw_icon(192, base / "icon-192x192.png")
    draw_icon(512, base / "icon-512x512.png")


if __name__ == "__main__":
    main()
