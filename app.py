import streamlit as st
from PIL import Image
import numpy as np
import os
import zipfile
import io

# Configuration
garments = {
    "tshirts": {"preview": "WHITE", "colors": ["WHITE"], "dark_colors": []}
}

st.title("👕 LynchMockup Tool v5 — Final Stable Manual Refresh")

uploaded_files = st.file_uploader("Upload PNG design files", type=["png"], accept_multiple_files=True)

if "settings" not in st.session_state:
    st.session_state.settings = {}
if "previews" not in st.session_state:
    st.session_state.previews = {}
if "refresh_flags" not in st.session_state:
    st.session_state.refresh_flags = {}

os.makedirs("temp_designs", exist_ok=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        design_name = uploaded_file.name.split('.')[0]
        path = f"temp_designs/{design_name}.png"
        with open(path, "wb") as f:
            f.write(uploaded_file.getvalue())

        st.subheader(f"Design: {design_name}")

        for garment, config in garments.items():
            key = f"{design_name}_{garment}"
            if key not in st.session_state.settings:
                st.session_state.settings[key] = {"scale": 100, "offset": 0}
            if key not in st.session_state.refresh_flags:
                st.session_state.refresh_flags[key] = False

            col1, col2 = st.columns(2)
            with col1:
                st.session_state.settings[key]["scale"] = st.slider("Scale", 50, 100, st.session_state.settings[key]["scale"], key=f"{key}_scale")
            with col2:
                st.session_state.settings[key]["offset"] = st.slider("Offset", -100, 100, st.session_state.settings[key]["offset"], key=f"{key}_offset")

            if st.button(f"🔁 Refresh {garment}", key=f"{key}_refresh"):
                st.session_state.refresh_flags[key] = True

            if st.session_state.refresh_flags[key]:
                design = Image.open(path).convert("RGBA")
                alpha = design.split()[-1]
                bbox = alpha.getbbox()
                cropped = design.crop(bbox)

                box_w, box_h = 400, 400
                target_w = int(box_w * (st.session_state.settings[key]["scale"] / 100))
                target_h = int(box_h * (st.session_state.settings[key]["scale"] / 100))
                aspect = cropped.width / cropped.height
                if aspect > (target_w / target_h):
                    new_w = target_w
                    new_h = int(new_w / aspect)
                else:
                    new_h = target_h
                    new_w = int(new_h * aspect)

                resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
                px = 200 + (box_w - new_w) // 2
                py = 300 + (box_h - new_h) // 2 + st.session_state.settings[key]["offset"]
                mockup = Image.new("RGBA", (800, 1000), "white")
                mockup.paste(resized, (px, py), resized)

                st.session_state.previews[key] = mockup.convert("RGB")
                st.session_state.refresh_flags[key] = False

            if key in st.session_state.previews:
                st.image(st.session_state.previews[key], caption=f"{garment} Preview")

# Export
if st.button("📦 Generate and Download ZIP"):
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for key, image in st.session_state.previews.items():
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="JPEG")
            zipf.writestr(f"{key}.jpg", img_bytes.getvalue())

    st.download_button("⬇️ Download ZIP", output_zip.getvalue(), file_name="mockups.zip", mime="application/zip")
