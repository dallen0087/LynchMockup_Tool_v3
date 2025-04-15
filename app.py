
import streamlit as st
from PIL import Image
import numpy as np
import zipfile
import io
import os

# Garment and color configuration
garments = {
    "tshirts": {
        "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "WHITE", "YELLOW"],
        "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]
    },
    "crop_tops": {
        "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "WHITE", "RED"],
        "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]
    },
    "hoodies": {
        "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "GREY", "YELLOW"],
        "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]
    },
    "sweatshirts": {
        "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "GREY", "YELLOW"],
        "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]
    },
    "ringer_tees": {
        "colors": ["BLACK-WHITE", "WHITE-BLACK", "WHITE-RED"],
        "dark_colors": ["BLACK-WHITE"]
    }
}

# UI Setup
st.title("👕 LynchMockup_Tool_v3")
st.write("Upload a transparent PNG design. It will be applied to each garment and exported as a ZIP.")

uploaded_file = st.file_uploader("Upload your design (PNG only)", type=["png"])
selected_guides = {}

# Guide selector per garment
for garment in garments:
    st.subheader(f"{garment.replace('_', ' ').title()}")
    guide_folder = f"assets/guides/{garment}"
    available_guides = [f.split(".")[0] for f in os.listdir(guide_folder) if f.endswith(".png")]
    selected = st.selectbox(f"Select guide for {garment}", available_guides, key=garment)
    selected_guides[garment] = selected

# Preview and export
if uploaded_file:
    st.subheader("Preview")
    design = Image.open(uploaded_file).convert("RGBA")
    alpha = design.split()[-1]
    bbox = alpha.getbbox()
    cropped = design.crop(bbox)

    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for garment, config in garments.items():
            guide_path = f"assets/guides/{garment}/{selected_guides[garment]}.png"
            guide = Image.open(guide_path).convert("RGBA")

            # Detect placement box
            alpha = np.array(guide.split()[-1])
            mask = alpha < 10
            ys, xs = np.where(mask)
            box_x0, box_y0, box_x1, box_y1 = xs.min(), ys.min(), xs.max(), ys.max()
            box_w, box_h = box_x1 - box_x0, box_y1 - box_y0

            # Resize to fit box
            aspect = cropped.width / cropped.height
            if aspect > (box_w / box_h):
                new_w = box_w
                new_h = int(new_w / aspect)
            else:
                new_h = box_h
                new_w = int(new_h * aspect)

            resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
            resized_alpha = resized.split()[-1]

            for color in config["colors"]:
                shirt_path = f"assets/{garment}/{color}.jpg"
                if not os.path.exists(shirt_path):
                    continue

                shirt = Image.open(shirt_path).convert("RGBA")
                fill_color = "white" if color in config["dark_colors"] else "black"
                fill = Image.new("RGBA", resized.size, color=fill_color)
                fill.putalpha(resized_alpha)

                px = box_x0 + (box_w - new_w) // 2
                py = box_y0 + (box_h - new_h) // 2
                composed = shirt.copy()
                composed.paste(fill, (px, py), fill)

                filename = f"{uploaded_file.name.split('.')[0]}_{garment}_{color}.jpg"
                img_bytes = io.BytesIO()
                composed.convert("RGB").save(img_bytes, format="JPEG")
                zipf.writestr(filename, img_bytes.getvalue())

    st.success("Mockups ready! Click below to download.")
    st.download_button("📦 Download ZIP", output_zip.getvalue(), file_name="mockups.zip", mime="application/zip")
