
import streamlit as st
from PIL import Image
import numpy as np
import zipfile
import io
import os

# Garment config
garments = {
    "tshirts": {
        "preview": "WHITE",
        "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "WHITE", "YELLOW"],
        "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]
    },
    "crop_tops": {
        "preview": "WHITE",
        "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "WHITE", "RED"],
        "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]
    },
    "hoodies": {
        "preview": "BLACK",
        "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "GREY", "YELLOW"],
        "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]
    },
    "sweatshirts": {
        "preview": "PINK",
        "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "GREY", "YELLOW"],
        "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]
    },
    "ringer_tees": {
        "preview": "WHITE-BLACK",
        "colors": ["BLACK-WHITE", "WHITE-BLACK", "WHITE-RED"],
        "dark_colors": ["BLACK-WHITE"]
    }
}

st.title("👕 LynchMockup_Tool_v3.6")
st.write("Upload multiple PNGs. Preview all garments. Export in one ZIP.")

color_mode = st.selectbox("🎨 Design Color Mode", [
    "Standard (Black/White)", "Blood Red", "Golden Orange", "Royal Blue", "Forest Green", "Unchanged"
])
color_hex_map = {
    "Blood Red": "#780606",
    "Golden Orange": "#FFA500",
    "Royal Blue": "#4169E1",
    "Forest Green": "#228B22"
}

# Controls
selected_guides = {}
include_garment = {}
for garment in garments:
    st.subheader(f"{garment.replace('_', ' ').title()}")
    include_garment[garment] = st.checkbox(f"Include in export", value=True, key=f"{garment}_check")
    guide_folder = f"assets/guides/{garment}"
    available_guides = sorted([f.split(".")[0] for f in os.listdir(guide_folder) if f.endswith(".png")])
    default_guide_index = available_guides.index("STANDARD") if "STANDARD" in available_guides else 0
    selected = st.selectbox("Select guide", available_guides, index=default_guide_index, key=f"{garment}_guide")
    selected_guides[garment] = selected

uploaded_files = st.file_uploader("Upload PNG design files", type=["png"], accept_multiple_files=True)

if uploaded_files:
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for uploaded_file in uploaded_files:
            design_name = uploaded_file.name.split('.')[0]
            design = Image.open(uploaded_file).convert("RGBA")
            alpha = design.split()[-1]
            bbox = alpha.getbbox()
            cropped = design.crop(bbox)

            st.markdown(f"### 🖼️ Previews for: `{design_name}`")
            cols = st.columns(len(garments))
            col_idx = 0

            for garment, config in garments.items():
                if not include_garment[garment]:
                    continue

                guide_path = f"assets/guides/{garment}/{selected_guides[garment]}.png"
                guide = Image.open(guide_path).convert("RGBA")

                alpha = np.array(guide.split()[-1])
                mask = alpha < 10
                ys, xs = np.where(mask)
                box_x0, box_y0, box_x1, box_y1 = xs.min(), ys.min(), xs.max(), ys.max()
                box_w, box_h = box_x1 - box_x0, box_y1 - box_y0

                aspect = cropped.width / cropped.height
                if aspect > (box_w / box_h):
                    new_w = box_w
                    new_h = int(new_w / aspect)
                else:
                    new_h = box_h
                    new_w = int(new_h * aspect)

                resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
                resized_alpha = resized.split()[-1]

                preview_color = config["preview"]
                preview_path = f"assets/{garment}/{preview_color}.jpg"
                preview_shirt = Image.open(preview_path).convert("RGBA")

                if color_mode == "Unchanged":
                    fill = resized.copy()
                elif color_mode == "Standard (Black/White)":
                    fill_color = "white" if preview_color in config["dark_colors"] else "black"
                    fill = Image.new("RGBA", resized.size, color=fill_color)
                    fill.putalpha(resized_alpha)
                else:
                    fill = Image.new("RGBA", resized.size, color=color_hex_map[color_mode])
                    fill.putalpha(resized_alpha)

                px = box_x0 + (box_w - new_w) // 2
                py = box_y0 + (box_h - new_h) // 2
                composed_preview = preview_shirt.copy()
                composed_preview.paste(fill, (px, py), fill)

                with cols[col_idx]:
                    st.image(composed_preview.convert("RGB"), caption=garment.replace("_", " ").title())
                col_idx = (col_idx + 1) % len(cols)

                for color in config["colors"]:
                    shirt_path = f"assets/{garment}/{color}.jpg"
                    if not os.path.exists(shirt_path):
                        continue

                    shirt = Image.open(shirt_path).convert("RGBA")
                    if color_mode == "Unchanged":
                        fill = resized.copy()
                    elif color_mode == "Standard (Black/White)":
                        fill_color = "white" if color in config["dark_colors"] else "black"
                        fill = Image.new("RGBA", resized.size, color=fill_color)
                        fill.putalpha(resized_alpha)
                    else:
                        fill = Image.new("RGBA", resized.size, color=color_hex_map[color_mode])
                        fill.putalpha(resized_alpha)

                    composed = shirt.copy()
                    composed.paste(fill, (px, py), fill)
                    filename = f"{design_name}_{garment}_{color}.jpg"
                    img_bytes = io.BytesIO()
                    composed.convert("RGB").save(img_bytes, format="JPEG")
                    zipf.writestr(filename, img_bytes.getvalue())

    st.success("All mockups are ready! Click below to download.")
    st.download_button("📦 Download All Mockups (ZIP)", output_zip.getvalue(), file_name="all_mockups.zip", mime="application/zip")
