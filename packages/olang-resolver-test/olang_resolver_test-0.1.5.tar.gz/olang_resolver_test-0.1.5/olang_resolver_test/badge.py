# badge.py
from pathlib import Path
from datetime import datetime, timezone

def write_badge(resolver_dir: Path, passed: bool, resolver_name: str = "unknown"):
    status_text = "certified" if passed else "failed"
    badge_color = "#4c1" if passed else "#e05d44"  # green/red

    # Left: "o-lang", Right: "certified" or "failed"
    left_text = "o-lang"
    right_text = status_text

    # Fixed widths for consistency (like shields.io)
    left_width = 60
    right_width = max(70, len(right_text) * 7)
    total_width = left_width + right_width

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h{left_width}v20H0z"/>
    <path fill="{badge_color}" d="M{left_width} 0h{right_width}v20H{left_width}z"/>
    <path fill="url(#b)" d="M0 0h{total_width}v20H0z"/>
  </g>
  <g fill="#fff" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="6" y="15" fill="#010101" fill-opacity=".3">{left_text}</text>
    <text x="6" y="14">{left_text}</text>
    <text x="{left_width + 6}" y="15" fill="#010101" fill-opacity=".3">{right_text}</text>
    <text x="{left_width + 6}" y="14">{right_text}</text>
  </g>
</svg>"""

    # Save SVG
    svg_path = resolver_dir / "badge.svg"
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"🔖 SVG badge saved to {svg_path}")

    # Save detailed text badge (with name & date)
    txt_path = resolver_dir / "badge.txt"
    cert_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    txt_content = (
        f"O-lang Resolver: {resolver_name}\n"
        f"Status: {'CERTIFIED' if passed else 'FAILED'}\n"
        f"Date: {cert_date}\n"
    )
    txt_path.write_text(txt_content, encoding="utf-8")
    print(f"📄 Text badge saved to {txt_path}")