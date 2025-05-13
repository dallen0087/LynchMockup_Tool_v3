import streamlit as st
from PIL import Image
import numpy as np
import zipfile
import io
import os

st.set_page_config(layout="wide")
st.title("👕 LynchMockup_Tool v4.7 — Buffered UI / Manual Refresh / Max Stability")

garments = {
    "tshirts": {"preview": "WHITE", "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "WHITE", "YELLOW"], "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]},
    "crop_tops": {"preview": "WHITE", "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "WHITE", "RED"], "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]},
    "hoodies": {"preview": "BLACK", "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "GREY", "YELLOW"], "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]},
    "sweatshirts": {"preview": "PINK", "colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE", "PINK", "GREY", "YELLOW"], "dark_colors": ["BABY_BLUE", "BLACK", "GREEN", "MAROON", "NAVY_BLUE"]},
    "ringer_tees": {"preview": "WHITE-BLACK", "colors": ["BLACK-WHITE", "WHITE-BLACK", "WHITE-RED"], "dark_colors": ["BLACK-WHITE"]}
}

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
if "buffer_ui" not in st.session_state:
    st.session_state.buffer_ui = {}
if "copied_settings" not in st.session_state:
    st.session_state.copied_settings = {}
if "previews" not in st.session_state:
    st.session_state.previews = {}
if "rendered_once" not in st.session_state:
    st.session_state.rendered_once = {}

if uploaded_files:
    if not os.path.exists("temp_designs"):
        os.makedirs("temp_designs")
    for uploaded_file in uploaded_files:
        design_name = uploaded_file.name.split('.')[0]
        design_path = f"temp_designs/{design_name}.png"
        with open(design_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        design = Image.open(design_path).convert("RGBA")
        alpha = design.split()[-1]
        bbox = alpha.getbbox()
        cropped = design.crop(bbox)

        st.markdown(f"## Design: `{design_name}`")
        cols = st.columns(len(garments))
        col_idx = 0

        for garment, config in garments.items():
            combo_key = f"{design_name}_{garment}"
            if combo_key not in st.session_state.settings:
                st.session_state.settings[combo_key] = {"scale": 100, "offset": 0, "guide": "STANDARD"}
            if combo_key not in st.session_state.buffer_ui:
                st.session_state.buffer_ui[combo_key] = st.session_state.settings[combo_key].copy()
            if combo_key not in st.session_state.rendered_once:
                st.session_state.rendered_once[combo_key] = False

            buf = st.session_state.buffer_ui[combo_key]

            with st.expander(f"{garment.replace('_', ' ').title()} Settings for `{design_name}`", expanded=False):
                guide_folder = f"assets/guides/{garment}"
                available_guides = sorted([f.split(".")[0] for f in os.listdir(guide_folder) if f.endswith(".png")])
                buf["guide"] = st.selectbox("Guide", available_guides, index=available_guides.index(buf["guide"]), key=f"{combo_key}_guide")
                buf["scale"] = st.slider("Scale (%)", 50, 100, buf["scale"], key=f"{combo_key}_scale")
                buf["offset"] = st.slider("Offset (px)", -100, 100, buf["offset"], key=f"{combo_key}_offset")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📋 Copy {garment} Settings", key=f"{combo_key}_copy"):
                        st.session_state.copied_settings[garment] = buf.copy()
                        st.success(f"Copied settings for {garment}")
                with col2:
                    if st.button(f"📥 Paste to All {garment.title()}", key=f"{combo_key}_paste"):
                        if garment in st.session_state.copied_settings:
                            copied = st.session_state.copied_settings[garment]
                            for uf in uploaded_files:
                                other_key = f"{uf.name.split('.')[0]}_{garment}"
                                st.session_state.buffer_ui[other_key] = copied.copy()
                            st.success(f"Pasted to all {garment}")

                if st.button(f"🔁 Refresh {garment} Preview", key=f"{combo_key}_refresh"):
                    st.session_state.settings[combo_key] = buf.copy()
                    st.session_state.rendered_once[combo_key] = True

            if not st.session_state.rendered_once[combo_key]:
                st.session_state.rendered_once[combo_key] = True  # One-time render on load

            if st.session_state.rendered_once[combo_key]:
                settings = st.session_state.settings[combo_key]
                guide_path = f"assets/guides/{garment}/{settings['guide']}.png"
                guide = Image.open(guide_path).convert("RGBA")
                alpha = np.array(guide.split()[-1])
                mask = alpha < 10
                ys, xs = np.where(mask)
                box_x0, box_y0, box_x1, box_y1 = xs.min(), ys.min(), xs.max(), ys.max()
                box_w, box_h = box_x1 - box_x0, box_y1 - box_y0

                target_w = int(box_w * (settings["scale"] / 100))
                target_h = int(box_h * (settings["scale"] / 100))
                aspect = cropped.width / cropped.height
                new_w, new_h = (target_w, int(target_w / aspect)) if aspect > (target_w / target_h) else (int(target_h * aspect), target_h)
                resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
                resized_alpha = resized.split()[-1]

                preview_color = config["preview"]
                preview_path = f"assets/{garment}/{preview_color}.jpg"
                preview_shirt = Image.open(preview_path).convert("RGBA")

                if color_mode == "Unchanged":
                    fill = resized.copy()
                elif color_mode == "Standard (Black/White)":
                    fill_color = "white" if preview_color in config["dark_colors"] else "black"
                    fill = Image.new("RGBA", resized.size, fill_color)
                    fill.putalpha(resized_alpha)
                else:
                    fill = Image.new("RGBA", resized.size, color_hex_map[color_mode])
                    fill.putalpha(resized_alpha)

                px = box_x0 + (box_w - new_w) // 2
                py = box_y0 + (box_h - new_h) // 2 + settings["offset"]
                composed = preview_shirt.copy()
                composed.paste(fill, (px, py), fill)
                st.session_state.previews[combo_key] = composed.convert("RGB")

            with cols[col_idx]:
                st.image(st.session_state.previews.get(combo_key), caption=garment.replace("_", " ").title())
            col_idx = (col_idx + 1) % len(cols)

st.markdown("## 📦 Export All Mockups")
if st.button("📁 Generate and Download ZIP"):
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for key, img in st.session_state.previews.items():
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            zipf.writestr(f"{key}.jpg", img_bytes.getvalue())
    st.download_button("⬇️ Download ZIP", output_zip.getvalue(), file_name="mockups.zip", mime="application/zip")
