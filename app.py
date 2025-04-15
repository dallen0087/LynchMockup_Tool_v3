
import streamlit as st
from PIL import Image
import numpy as np
import os

# Garment config
garments = {
    "tshirts": {"preview": "WHITE", "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "WHITE", "YELLOW"], "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]},
    "crop_tops": {"preview": "WHITE", "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "WHITE", "RED"], "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]},
    "hoodies": {"preview": "BLACK", "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "GREY", "YELLOW"], "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]},
    "sweatshirts": {"preview": "PINK", "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "GREY", "YELLOW"], "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]},
    "ringer_tees": {"preview": "WHITE-BLACK", "colors": ["BLACK-WHITE", "WHITE-BLACK", "WHITE-RED"], "dark_colors": ["BLACK-WHITE"]}
}

st.title("👕 LynchMockup_Tool v4.1 — Per-Design + Garment Control")

color_mode = st.selectbox("🎨 Design Color Mode", [
    "Standard (Black/White)", "Blood Red", "Golden Orange", "Royal Blue", "Forest Green", "Unchanged"
])
color_hex_map = {
    "Blood Red": "#780606",
    "Golden Orange": "#FFA500",
    "Royal Blue": "#4169E1",
    "Forest Green": "#228B22"
}

uploaded_files = st.file_uploader("Upload PNG design files", type=["png"], accept_multiple_files=True)

if "settings" not in st.session_state:
    st.session_state.settings = {}
if "previews" not in st.session_state:
    st.session_state.previews = {}
if "refresh_flags" not in st.session_state:
    st.session_state.refresh_flags = {}

if uploaded_files:
    for uploaded_file in uploaded_files:
        design_name = uploaded_file.name.split('.')[0]
        design = Image.open(uploaded_file).convert("RGBA")
        alpha = design.split()[-1]
        bbox = alpha.getbbox()
        cropped = design.crop(bbox)

        st.markdown(f"## 🎨 Design: `{design_name}`")

        cols = st.columns(len(garments))
        col_idx = 0

        for garment, config in garments.items():
            combo_key = f"{design_name}_{garment}"
            if combo_key not in st.session_state.settings:
                st.session_state.settings[combo_key] = {"scale": 100, "offset": 0, "guide": "STANDARD"}
            if combo_key not in st.session_state.refresh_flags:
                st.session_state.refresh_flags[combo_key] = False

            with st.expander(f"{garment.replace('_', ' ').title()} Settings for `{design_name}`", expanded=False):
                guide_folder = f"assets/guides/{garment}"
                available_guides = sorted([f.split(".")[0] for f in os.listdir(guide_folder) if f.endswith(".png")])
                selected_guide = st.selectbox("Select Guide", available_guides, index=available_guides.index("STANDARD"), key=f"{combo_key}_guide")
                st.session_state.settings[combo_key]["guide"] = selected_guide

                scale = st.slider("Scale within placement box (%)", 50, 100, st.session_state.settings[combo_key]["scale"], key=f"{combo_key}_scale")
                offset = st.slider("Vertical offset (px)", -100, 100, st.session_state.settings[combo_key]["offset"], key=f"{combo_key}_offset")
                st.session_state.settings[combo_key]["scale"] = scale
                st.session_state.settings[combo_key]["offset"] = offset

                if st.button(f"🔁 Refresh {garment} for {design_name}", key=f"{combo_key}_refresh"):
                    st.session_state.refresh_flags[combo_key] = True

            refresh = st.session_state.refresh_flags[combo_key]
            if refresh or combo_key not in st.session_state.previews:
                guide_path = f"assets/guides/{garment}/{st.session_state.settings[combo_key]['guide']}.png"
                guide = Image.open(guide_path).convert("RGBA")
                alpha = np.array(guide.split()[-1])
                mask = alpha < 10
                ys, xs = np.where(mask)
                box_x0, box_y0, box_x1, box_y1 = xs.min(), ys.min(), xs.max(), ys.max()
                box_w, box_h = box_x1 - box_x0, box_y1 - box_y0

                target_w = int(box_w * (scale / 100))
                target_h = int(box_h * (scale / 100))
                aspect = cropped.width / cropped.height
                if aspect > (target_w / target_h):
                    new_w = target_w
                    new_h = int(new_w / aspect)
                else:
                    new_h = target_h
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
                py = box_y0 + (box_h - new_h) // 2 + offset
                composed_preview = preview_shirt.copy()
                composed_preview.paste(fill, (px, py), fill)

                st.session_state.previews[combo_key] = composed_preview.convert("RGB")
                st.session_state.refresh_flags[combo_key] = False

            with cols[col_idx]:
                st.image(st.session_state.previews[combo_key], caption=f"{garment.replace('_', ' ').title()}")
            col_idx = (col_idx + 1) % len(cols)

import zipfile
import io
import os

# Save uploaded images to disk so they can be reopened during export
if not os.path.exists("temp_designs"):
    os.makedirs("temp_designs")

for uploaded_file in uploaded_files:
    design_name = uploaded_file.name.split('.')[0]
    design_path = f"temp_designs/{design_name}.png"
    with open(design_path, "wb") as f:
        f.write(uploaded_file.read())

# Export logic
st.markdown("## 📦 Export All Mockups")

if st.button("📁 Generate and Download ZIP"):
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for combo_key, preview_img in st.session_state.previews.items():
            design_name, garment = combo_key.split("_", 1)
            for color in garments[garment]["colors"]:
                preview_color = color
                preview_path = f"assets/{garment}/{preview_color}.jpg"
                if not os.path.exists(preview_path):
                    continue

                shirt = Image.open(preview_path).convert("RGBA")
                scale = st.session_state.settings[combo_key]["scale"]
                offset_y = st.session_state.settings[combo_key]["offset"]
                guide_name = st.session_state.settings[combo_key]["guide"]
                guide_path = f"assets/guides/{garment}/{guide_name}.png"

                guide = Image.open(guide_path).convert("RGBA")
                alpha = np.array(guide.split()[-1])
                mask = alpha < 10
                ys, xs = np.where(mask)
                box_x0, box_y0, box_x1, box_y1 = xs.min(), ys.min(), xs.max(), ys.max()
                box_w, box_h = box_x1 - box_x0, box_y1 - box_y0

                design = Image.open(f"temp_designs/{design_name}.png").convert("RGBA")
                alpha = design.split()[-1]
                bbox = alpha.getbbox()
                cropped = design.crop(bbox)

                target_w = int(box_w * (scale / 100))
                target_h = int(box_h * (scale / 100))
                aspect = cropped.width / cropped.height
                if aspect > (target_w / target_h):
                    new_w = target_w
                    new_h = int(new_w / aspect)
                else:
                    new_h = target_h
                    new_w = int(new_h * aspect)

                resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
                resized_alpha = resized.split()[-1]

                if color_mode == "Unchanged":
                    fill = resized.copy()
                elif color_mode == "Standard (Black/White)":
                    fill_color = "white" if color in garments[garment]["dark_colors"] else "black"
                    fill = Image.new("RGBA", resized.size, color=fill_color)
                    fill.putalpha(resized_alpha)
                else:
                    fill = Image.new("RGBA", resized.size, color=color_hex_map[color_mode])
                    fill.putalpha(resized_alpha)

                px = box_x0 + (box_w - new_w) // 2
                py = box_y0 + (box_h - new_h) // 2 + offset_y
                composed = shirt.copy()
                composed.paste(fill, (px, py), fill)

                filename = f"{design_name}_{garment}_{color}.jpg"
                img_bytes = io.BytesIO()
                composed.convert("RGB").save(img_bytes, format="JPEG")
                zipf.writestr(filename, img_bytes.getvalue())

    st.download_button("⬇️ Download ZIP", output_zip.getvalue(), file_name="mockups.zip", mime="application/zip")
