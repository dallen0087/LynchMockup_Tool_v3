import streamlit as st
from PIL import Image
import numpy as np
import zipfile
import io
import os

st.set_page_config(layout="wide")
st.title("👕 LynchMockup_Tool v5.3 — Manual Refresh + Master Refresh")

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
if "previews" not in st.session_state:
    st.session_state.previews = {}
if "copied_settings" not in st.session_state:
    st.session_state.copied_settings = {}
if "has_rendered_once" not in st.session_state:
    st.session_state.has_rendered_once = {}

def render_preview(cropped, guide_img, shirt_img, settings, color_mode, dark_colors, hex_map):
    alpha = np.array(guide_img.split()[-1])
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

    if color_mode == "Unchanged":
        fill = resized.copy()
    elif color_mode == "Standard (Black/White)":
        fill_color = "white" if settings["preview"] in dark_colors else "black"
        fill = Image.new("RGBA", resized.size, fill_color)
        fill.putalpha(resized_alpha)
    else:
        fill = Image.new("RGBA", resized.size, hex_map[color_mode])
        fill.putalpha(resized_alpha)

    px = box_x0 + (box_w - new_w) // 2
    py = box_y0 + (box_h - new_h) // 2 + settings["offset"]
    composed = shirt_img.copy()
    composed.paste(fill, (px, py), fill)
    return composed.convert("RGB")
if uploaded_files:
    if not os.path.exists("temp_designs"):
        os.makedirs("temp_designs")

    tabs = st.tabs([f"{uf.name.split('.')[0]}" for uf in uploaded_files])
    refresh_queue = []

    for tab, uploaded_file in zip(tabs, uploaded_files):
        with tab:
            design_name = uploaded_file.name.split('.')[0]
            design_path = f"temp_designs/{design_name}.png"
            with open(design_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            design = Image.open(design_path).convert("RGBA")
            alpha = design.split()[-1]
            bbox = alpha.getbbox()
            cropped = design.crop(bbox)

            st.markdown(f"### Design: `{design_name}`")
            cols = st.columns(len(garments))
            col_idx = 0

            for garment, config in garments.items():
                combo_key = f"{design_name}_{garment}"
                if combo_key not in st.session_state.settings:
                    st.session_state.settings[combo_key] = {"scale": 100, "offset": 0, "guide": "STANDARD", "preview": config["preview"]}
                if combo_key not in st.session_state.buffer_ui:
                    st.session_state.buffer_ui[combo_key] = st.session_state.settings[combo_key].copy()
                if combo_key not in st.session_state.has_rendered_once:
                    guide_img = Image.open(f"assets/guides/{garment}/STANDARD.png").convert("RGBA")
                    shirt_img = Image.open(f"assets/{garment}/{config['preview']}.jpg").convert("RGBA")
                    st.session_state.previews[combo_key] = render_preview(
                        cropped, guide_img, shirt_img, st.session_state.settings[combo_key],
                        color_mode, config["dark_colors"], color_hex_map
                    )
                    st.session_state.has_rendered_once[combo_key] = True

                buf = st.session_state.buffer_ui[combo_key]
                with st.expander(f"{garment.replace('_', ' ').title()} Settings for `{design_name}`", expanded=False):
                    guide_folder = f"assets/guides/{garment}"
                    guides = sorted([f.split(".")[0] for f in os.listdir(guide_folder) if f.endswith(".png")])
                    buf["guide"] = st.selectbox("Guide", guides, index=guides.index(buf["guide"]), key=f"{combo_key}_guide")
                    buf["scale"] = st.slider("Scale (%)", 50, 100, buf["scale"], key=f"{combo_key}_scale")
                    buf["offset"] = st.slider("Offset (px)", -100, 100, buf["offset"], key=f"{combo_key}_offset")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"📋 Copy {garment} Settings", key=f"{combo_key}_copy"):
                            st.session_state.copied_settings[garment] = buf.copy()
                            st.success("Copied settings")
                    with col2:
                        if st.button(f"📥 Paste to All {garment.title()}", key=f"{combo_key}_paste"):
                            for uf2 in uploaded_files:
                                other_key = f"{uf2.name.split('.')[0]}_{garment}"
                                st.session_state.buffer_ui[other_key] = st.session_state.copied_settings[garment].copy()
                            st.success("Pasted settings")

                    if st.button(f"🔁 Refresh {garment} Preview", key=f"{combo_key}_refresh"):
                        st.session_state.settings[combo_key] = buf.copy()
                        guide_img = Image.open(f"assets/guides/{garment}/{buf['guide']}.png").convert("RGBA")
                        shirt_img = Image.open(f"assets/{garment}/{config['preview']}.jpg").convert("RGBA")
                        st.session_state.previews[combo_key] = render_preview(
                            cropped, guide_img, shirt_img, buf, color_mode, config["dark_colors"], color_hex_map
                        )

                if combo_key in st.session_state.previews:
                    with cols[col_idx]:
                        st.image(st.session_state.previews[combo_key], caption=garment.replace("_", " ").title())
                col_idx = (col_idx + 1) % len(cols)

    st.markdown("## 🔁 Master Refresh")
    if st.button("🔁 Refresh All Adjusted Previews"):
        for combo_key, buf in st.session_state.buffer_ui.items():
            if combo_key not in st.session_state.settings:
                continue
            if buf != st.session_state.settings[combo_key]:
                design_name, garment = combo_key.split("_", 1)
                design_path = f"temp_designs/{design_name}.png"
                design = Image.open(design_path).convert("RGBA")
                alpha = design.split()[-1]
                bbox = alpha.getbbox()
                cropped = design.crop(bbox)
                guide_img = Image.open(f"assets/guides/{garment}/{buf['guide']}.png").convert("RGBA")
                shirt_img = Image.open(f"assets/{garment}/{buf['preview']}.jpg").convert("RGBA")
                st.session_state.previews[combo_key] = render_preview(
                    cropped, guide_img, shirt_img, buf, color_mode, garments[garment]["dark_colors"], color_hex_map
                )
                st.session_state.settings[combo_key] = buf.copy()
        st.success("All adjusted previews refreshed.")

    st.markdown("## 📦 Export All Mockups")
    if st.button("📁 Generate and Download ZIP"):
        output_zip = io.BytesIO()
        with zipfile.ZipFile(output_zip, 'w') as zipf:
            for key, img in st.session_state.previews.items():
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="JPEG")
                zipf.writestr(f"{key}.jpg", img_bytes.getvalue())
        st.download_button("⬇️ Download ZIP", output_zip.getvalue(), file_name="mockups.zip", mime="application/zip")
