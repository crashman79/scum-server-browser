#!/usr/bin/env python3
"""Generate app icon representing SCUM Server Browser"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create icon directory if it doesn't exist
icon_dir = os.path.join(os.path.dirname(__file__), "scum_tracker", "assets")
os.makedirs(icon_dir, exist_ok=True)

# Create icon image (256x256 for high quality)
size = 256
img = Image.new('RGB', (size, size), color=(20, 20, 30))  # Dark background (SCUM-ish)
draw = ImageDraw.Draw(img)

# Draw a globe/network circle (representing server browser)
circle_radius = 80
circle_x = size // 2 - circle_radius
circle_y = size // 2 - circle_radius
draw.ellipse(
    [circle_x, circle_y, circle_x + circle_radius * 2, circle_y + circle_radius * 2],
    outline=(100, 200, 255),  # Cyan/blue
    width=6
)

# Draw network nodes around the circle
import math
num_nodes = 8
node_radius = 8
outer_radius = circle_radius + 30

for i in range(num_nodes):
    angle = (i / num_nodes) * 2 * math.pi
    x = size // 2 + outer_radius * math.cos(angle)
    y = size // 2 + outer_radius * math.sin(angle)
    
    # Draw node
    draw.ellipse(
        [x - node_radius, y - node_radius, x + node_radius, y + node_radius],
        fill=(100, 200, 255),
        outline=(200, 200, 255),
        width=2
    )
    
    # Draw connection line to center
    draw.line(
        [(size // 2, size // 2), (x, y)],
        fill=(100, 150, 200),
        width=2
    )

# Draw center point (server hub)
hub_radius = 12
center_x = size // 2
center_y = size // 2
draw.ellipse(
    [center_x - hub_radius, center_y - hub_radius, center_x + hub_radius, center_y + hub_radius],
    fill=(255, 150, 0),  # Orange for emphasis
    outline=(255, 200, 100),
    width=3
)

# Save in multiple sizes for different uses
icon_path = os.path.join(icon_dir, "app_icon.png")
img.save(icon_path)
print(f"✓ Generated icon: {icon_path}")

# Create smaller versions
for size_name, size_px in [("64", 64), ("32", 32), ("16", 16)]:
    resized = img.resize((size_px, size_px), Image.Resampling.LANCZOS)
    resized_path = os.path.join(icon_dir, f"app_icon_{size_name}.png")
    resized.save(resized_path)
    print(f"✓ Generated icon: {resized_path}")
