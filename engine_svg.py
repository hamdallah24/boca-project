import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional
from PIL import Image

SCENE_W, SCENE_H = 1350, 2400


def _find_chromium() -> str:
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError("Chromium/Chrome binary not found in PATH.")


def render_svg_to_rgba(
    svg_body: str,
    width: int,
    height: int,
    cache_dir: str = ".cache/svg_layers",
    viewbox_w: Optional[int] = None,
    viewbox_h: Optional[int] = None,
) -> Image.Image:
    """Rasterize SVG string via Chromium headless with disk caching."""
    vw = viewbox_w or width
    vh = viewbox_h or height
    key = hashlib.sha256(f"{width}x{height}:{vw}x{vh}:{svg_body}".encode("utf-8")).hexdigest()[:20]
    os.makedirs(cache_dir, exist_ok=True)
    cached_png = Path(cache_dir) / f"{key}.png"

    if cached_png.exists():
        return Image.open(cached_png).convert("RGBA")

    chromium = _find_chromium()
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  html, body {{ margin: 0; padding: 0; width: {width}px; height: {height}px; overflow: hidden; background: transparent; }}
  svg {{ display: block; width: {width}px; height: {height}px; }}
</style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {vw} {vh}">
{svg_body}
</svg>
</body>
</html>"""

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "render.html"
        out_path = Path(tmp) / "out.png"
        html_path.write_text(html, encoding="utf-8")

        cmd = [
            chromium,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--default-background-color=00000000",
            "--force-device-scale-factor=1",
            f"--window-size={width},{height}",
            f"--screenshot={out_path}",
            html_path.as_uri(),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        img = Image.open(out_path).convert("RGBA")
        img.save(cached_png, "PNG")
        return img


# ==============================================================================
# CRISP OUTLINED VECTOR SCENES (1350 x 2400, ground plane at y ~ 1360-1400)
# ==============================================================================

def _svg_city_street() -> Dict[str, str]:
    sky = """
    <defs>
      <linearGradient id="skyG" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#38BDF8"/>
        <stop offset="65%" stop-color="#BAE6FD"/>
        <stop offset="100%" stop-color="#E0F2FE"/>
      </linearGradient>
    </defs>
    <rect width="1350" height="2400" fill="url(#skyG)"/>
    <circle cx="1110" cy="310" r="145" fill="#FEF08A" opacity="0.45"/>
    <circle cx="1110" cy="310" r="95" fill="#FACC15" stroke="#1E293B" stroke-width="5"/>
    """

    clouds = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round" fill="#FFFFFF">
      <path d="M130,360 Q130,305 185,305 Q210,255 275,260 Q335,265 355,315 Q405,320 405,365 Z"/>
      <path d="M560,240 Q560,195 605,195 Q630,150 690,155 Q745,160 760,205 Q805,210 805,245 Z"/>
      <path d="M900,470 Q900,425 945,425 Q965,380 1020,385 Q1075,390 1090,430 Q1135,435 1135,470 Z"/>
    </g>
    """

    midground = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round">
      <!-- Distant silhouette buildings -->
      <rect x="40" y="690" width="220" height="690" rx="8" fill="#93C5FD"/>
      <rect x="290" y="560" width="260" height="820" rx="8" fill="#BFDBFE"/>
      <rect x="590" y="640" width="210" height="740" rx="8" fill="#93C5FD"/>
      <rect x="830" y="510" width="270" height="870" rx="8" fill="#A5B4FC"/>
      <rect x="1130" y="660" width="190" height="720" rx="8" fill="#93C5FD"/>

      <!-- Windows -->
      <g fill="#FEF9C3" stroke-width="3">
        <rect x="75" y="740" width="55" height="65" rx="4"/><rect x="165" y="740" width="55" height="65" rx="4"/>
        <rect x="75" y="845" width="55" height="65" rx="4"/><rect x="165" y="845" width="55" height="65" rx="4"/>
        <rect x="330" y="610" width="60" height="70" rx="4"/><rect x="435" y="610" width="60" height="70" rx="4"/>
        <rect x="330" y="720" width="60" height="70" rx="4"/><rect x="435" y="720" width="60" height="70" rx="4"/>
        <rect x="330" y="830" width="60" height="70" rx="4"/><rect x="435" y="830" width="60" height="70" rx="4"/>
        <rect x="875" y="565" width="65" height="70" rx="4"/><rect x="985" y="565" width="65" height="70" rx="4"/>
        <rect x="875" y="675" width="65" height="70" rx="4"/><rect x="985" y="675" width="65" height="70" rx="4"/>
        <rect x="875" y="785" width="65" height="70" rx="4"/><rect x="985" y="785" width="65" height="70" rx="4"/>
      </g>

      <!-- Crisp Vector Street Trees -->
      <rect x="218" y="1160" width="28" height="210" fill="#92400E"/>
      <circle cx="232" cy="1120" r="88" fill="#22C55E"/>
      <circle cx="195" cy="1150" r="56" fill="#4ADE80"/>

      <rect x="1085" y="1170" width="28" height="200" fill="#92400E"/>
      <circle cx="1099" cy="1130" r="82" fill="#22C55E"/>
      <circle cx="1135" cy="1155" r="52" fill="#4ADE80"/>

      <!-- Street Lamp -->
      <rect x="665" y="910" width="16" height="460" fill="#475569"/>
      <path d="M665,915 L735,915 L735,940 L681,940 Z" fill="#475569"/>
      <ellipse cx="725" cy="952" rx="28" ry="14" fill="#FDE047"/>
    </g>
    """

    ground = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round">
      <!-- Grass strip -->
      <rect x="-10" y="1335" width="1370" height="45" fill="#4ADE80"/>
      <!-- Sidewalk -->
      <rect x="-10" y="1375" width="1370" height="150" fill="#CBD5E1"/>
      <line x1="250" y1="1375" x2="210" y2="1525" stroke-width="4"/>
      <line x1="580" y1="1375" x2="570" y2="1525" stroke-width="4"/>
      <line x1="910" y1="1375" x2="930" y2="1525" stroke-width="4"/>
      <line x1="1200" y1="1375" x2="1240" y2="1525" stroke-width="4"/>
      <!-- Curb -->
      <rect x="-10" y="1515" width="1370" height="30" fill="#94A3B8"/>
      <!-- Asphalt Road -->
      <rect x="-10" y="1545" width="1370" height="865" fill="#475569"/>
      <!-- Road dashes -->
      <g fill="#FACC15" stroke-width="4">
        <rect x="70" y="1760" width="150" height="28" rx="6"/>
        <rect x="370" y="1760" width="150" height="28" rx="6"/>
        <rect x="670" y="1760" width="150" height="28" rx="6"/>
        <rect x="970" y="1760" width="150" height="28" rx="6"/>
        <rect x="1240" y="1760" width="150" height="28" rx="6"/>
      </g>
    </g>
    """
    return {"sky": sky, "clouds": clouds, "midground": midground, "ground": ground}


def _svg_classroom() -> Dict[str, str]:
    sky = """
    <rect width="1350" height="2400" fill="#FEF3C7"/>
    <rect x="0" y="1060" width="1350" height="310" fill="#FDE68A" stroke="#1E293B" stroke-width="5"/>
    """
    clouds = ""  # Classroom interior has no drifting clouds
    midground = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round">
      <!-- Window -->
      <rect x="85" y="450" width="250" height="360" rx="10" fill="#BAE6FD"/>
      <circle cx="265" cy="530" r="38" fill="#FACC15" stroke-width="4"/>
      <path d="M85,730 Q180,690 335,725 L335,810 L85,810 Z" fill="#4ADE80"/>
      <line x1="210" y1="450" x2="210" y2="810" stroke-width="5"/>
      <line x1="85" y1="630" x2="335" y2="630" stroke-width="5"/>
      <rect x="70" y="805" width="280" height="28" rx="6" fill="#D97706"/>

      <!-- Chalkboard -->
      <rect x="405" y="410" width="840" height="490" rx="14" fill="#B45309"/>
      <rect x="435" y="440" width="780" height="430" rx="6" fill="#166534"/>
      <!-- Chalk tray & chalk -->
      <rect x="480" y="885" width="220" height="22" rx="4" fill="#92400E"/>
      <rect x="510" y="875" width="42" height="12" rx="3" fill="#FFFFFF" stroke-width="3"/>
      <rect x="570" y="875" width="42" height="12" rx="3" fill="#FDE047" stroke-width="3"/>

      <!-- Bookshelf on right -->
      <rect x="1080" y="960" width="220" height="400" rx="8" fill="#D97706"/>
      <rect x="1100" y="985" width="180" height="105" fill="#92400E"/>
      <rect x="1100" y="1115" width="180" height="105" fill="#92400E"/>
      <!-- Books -->
      <rect x="1115" y="1010" width="32" height="80" fill="#EF4444" stroke-width="3"/>
      <rect x="1149" y="1000" width="30" height="90" fill="#3B82F6" stroke-width="3"/>
      <rect x="1181" y="1020" width="34" height="70" fill="#FACC15" stroke-width="3"/>
    </g>
    """
    ground = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round">
      <rect x="-10" y="1360" width="1370" height="1050" fill="#D97706"/>
      <line x1="-10" y1="1490" x2="1360" y2="1490" stroke-width="4"/>
      <line x1="-10" y1="1650" x2="1360" y2="1650" stroke-width="4"/>
      <line x1="-10" y1="1840" x2="1360" y2="1840" stroke-width="4"/>
      <line x1="340" y1="1360" x2="290" y2="1490" stroke-width="4"/>
      <line x1="890" y1="1360" x2="940" y2="1490" stroke-width="4"/>
      <line x1="560" y1="1490" x2="520" y2="1650" stroke-width="4"/>
      <line x1="1080" y1="1490" x2="1140" y2="1650" stroke-width="4"/>
    </g>
    """
    return {"sky": sky, "clouds": clouds, "midground": midground, "ground": ground}


def _svg_mountain_sunset() -> Dict[str, str]:
    sky = """
    <defs>
      <linearGradient id="sunSet" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#5B21B6"/>
        <stop offset="50%" stop-color="#C026D3"/>
        <stop offset="85%" stop-color="#F97316"/>
        <stop offset="100%" stop-color="#FDE047"/>
      </linearGradient>
    </defs>
    <rect width="1350" height="2400" fill="url(#sunSet)"/>
    <circle cx="1020" cy="480" r="170" fill="#FDE047" opacity="0.3"/>
    <circle cx="1020" cy="480" r="105" fill="#FEF08A" stroke="#1E293B" stroke-width="5"/>
    """
    clouds = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round" fill="#FED7AA">
      <path d="M160,400 Q160,350 215,350 Q245,305 310,310 Q365,315 385,360 Q435,365 435,400 Z"/>
      <path d="M720,310 Q720,265 765,265 Q790,220 850,225 Q900,230 915,275 Q960,280 960,310 Z"/>
    </g>
    """
    midground = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round">
      <!-- Distant mountains -->
      <polygon points="-20,1370 280,830 590,1370" fill="#7C3AED"/>
      <polygon points="360,1370 720,760 1120,1370" fill="#6D28D9"/>
      <polygon points="840,1370 1180,870 1400,1370" fill="#5B21B6"/>
      <!-- Midground rice-field / green valley -->
      <rect x="-10" y="1220" width="1370" height="160" fill="#15803D"/>
      <!-- Small wooden hut -->
      <rect x="130" y="1140" width="140" height="100" fill="#B45309"/>
      <polygon points="105,1150 200,1065 295,1150" fill="#D97706"/>
    </g>
    """
    ground = """
    <g stroke="#1E293B" stroke-width="5" stroke-linejoin="round">
      <path d="M-10,1370 Q675,1335 1360,1370 L1360,2410 L-10,2410 Z" fill="#92400E"/>
      <path d="M-10,1370 Q675,1335 1360,1370 L1360,1415 Q675,1380 -10,1415 Z" fill="#22C55E"/>
    </g>
    """
    return {"sky": sky, "clouds": clouds, "midground": midground, "ground": ground}


SCENE_BUILDERS = {
    "city_street": _svg_city_street,
    "classroom": _svg_classroom,
    "mountain_sunset": _svg_mountain_sunset,
}


def build_parallax_scene(scene_name: str) -> Dict[str, Optional[Image.Image]]:
    builder = SCENE_BUILDERS.get(scene_name, _svg_city_street)
    svg_dict = builder()
    layers: Dict[str, Optional[Image.Image]] = {}
    for layer_name, svg_body in svg_dict.items():
        if not svg_body.strip():
            layers[layer_name] = None
        else:
            layers[layer_name] = render_svg_to_rgba(svg_body, SCENE_W, SCENE_H)
    return layers


# ==============================================================================
# CRISP OUTLINED VECTOR PROPS (512 x 512 base, scaled dynamically)
# ==============================================================================

PROP_SVGS = {
    "phone_scroll": """
    <g stroke="#1E293B" stroke-width="10" stroke-linejoin="round">
      <rect x="126" y="36" width="260" height="440" rx="34" fill="#334155"/>
      <rect x="148" y="76" width="216" height="352" rx="14" fill="#F8FAFC"/>
      <rect x="216" y="50" width="80" height="12" rx="6" fill="#0F172A" stroke="none"/>
      <circle cx="256" cy="452" r="14" fill="#64748B" stroke-width="6"/>
    </g>
    """,
    "clock_face": """
    <g stroke="#1E293B" stroke-width="12" stroke-linejoin="round">
      <circle cx="256" cy="256" r="205" fill="#EF4444"/>
      <circle cx="256" cy="256" r="172" fill="#FFFFFF"/>
      <line x1="256" y1="106" x2="256" y2="128" stroke-linecap="round"/>
      <line x1="256" y1="384" x2="256" y2="406" stroke-linecap="round"/>
      <line x1="106" y1="256" x2="128" y2="256" stroke-linecap="round"/>
      <line x1="384" y1="256" x2="406" y2="256" stroke-linecap="round"/>
    </g>
    """,
    "hourglass": """
    <g stroke="#1E293B" stroke-width="10" stroke-linejoin="round">
      <rect x="120" y="56" width="272" height="36" rx="10" fill="#B45309"/>
      <rect x="120" y="420" width="272" height="36" rx="10" fill="#B45309"/>
      <path d="M156,92 L356,92 C356,195 276,225 276,256 C276,287 356,317 356,420 L156,420 C156,317 236,287 236,256 C236,225 156,195 156,92 Z" fill="#E0F2FE"/>
      <path d="M182,160 L330,160 C315,205 268,230 256,248 C244,230 197,205 182,160 Z" fill="#FACC15" stroke="none"/>
      <path d="M174,415 L338,415 C325,365 280,350 256,350 C232,350 187,365 174,415 Z" fill="#FACC15" stroke="none"/>
    </g>
    """,
    "lightbulb": """
    <g stroke="#1E293B" stroke-width="10" stroke-linejoin="round" stroke-linecap="round">
      <line x1="256" y1="28" x2="256" y2="66" stroke="#FACC15" stroke-width="14"/>
      <line x1="102" y1="92" x2="132" y2="122" stroke="#FACC15" stroke-width="14"/>
      <line x1="410" y1="92" x2="380" y2="122" stroke="#FACC15" stroke-width="14"/>
      <line x1="56" y1="226" x2="96" y2="226" stroke="#FACC15" stroke-width="14"/>
      <line x1="456" y1="226" x2="416" y2="226" stroke="#FACC15" stroke-width="14"/>
      <path d="M152,226 A104,104 0 1 1 360,226 C360,275 322,305 316,352 L196,352 C190,305 152,275 152,226 Z" fill="#FDE047"/>
      <rect x="196" y="352" width="120" height="32" rx="8" fill="#94A3B8"/>
      <rect x="206" y="384" width="100" height="30" rx="8" fill="#64748B"/>
      <path d="M224,414 L288,414 L274,442 L238,442 Z" fill="#334155"/>
    </g>
    """,
    "coin_stack": """
    <g stroke="#1E293B" stroke-width="9" stroke-linejoin="round">
      <ellipse cx="256" cy="390" rx="135" ry="44" fill="#CA8A04"/>
      <path d="M121,346 L121,390 A135,44 0 0 0 391,390 L391,346 Z" fill="#EAB308"/>
      <ellipse cx="256" cy="346" rx="135" ry="44" fill="#FACC15"/>
      <path d="M121,292 L121,336 A135,44 0 0 0 391,336 L391,292 Z" fill="#EAB308"/>
      <ellipse cx="256" cy="292" rx="135" ry="44" fill="#FACC15"/>
      <path d="M121,238 L121,282 A135,44 0 0 0 391,282 L391,238 Z" fill="#EAB308"/>
      <ellipse cx="256" cy="238" rx="135" ry="44" fill="#FEF08A"/>
      <text x="256" y="254" font-family="sans-serif" font-weight="900" font-size="48" fill="#92400E" stroke="none" text-anchor="middle">Rp</text>
    </g>
    """,
}


def build_prop_sprites() -> Dict[str, Image.Image]:
    return {name: render_svg_to_rgba(svg, 512, 512) for name, svg in PROP_SVGS.items()}