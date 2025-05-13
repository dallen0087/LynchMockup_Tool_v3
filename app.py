import streamlit as st
from PIL import Image
import numpy as np
import io
import os
import zipfile

# Define garments
garments = {
    "tshirts": {"preview": "WHITE", "colors": ["WHITE"], "dark_colors": []}
}

st.title("👕 LynchMockup Tool v5 — Final MATRIX Stable")

uploaded_files = st.file_uploader("Upload PNGs", type=["png"], accept_multiple_files=True)

if "settings" not in st.session_state:
    st.session_state.settings = {}
if "previews" not in st.session_state:
    st.session_state.previews = {}
if "copied" not in st.session_state:
    st.session_state.copied = {}

os.makedirs("temp_designs", exist_ok=True)

if uploaded_files:
    for file in uploaded_files:
        name = file.name.split(".")[0]
        path = f"temp_designs/{name}.png"
        with open(path, "wb") as f:
            f.write(file.getvalue())

        st.header(name)

        for garment, conf in garments.items():
            key = f"{name}_{garment}"
            if key not in st.session_state.settings:
                st.session_state.settings[key] = {"scale": 100, "offset": 0}

            scale = st.slider("Scale", 50, 100, st.session_state.settings[key]["scale"], key=f"{key}_scale")
            offset = st.slider("Offset", -100, 100, st.session_state.settings[key]["offset"], key=f"{key}_offset")
            st.session_state.settings[key]["scale"] = scale
            st.session_state.settings[key]["offset"] = offset

            cols = st.columns(2)
            if cols[0].button("📋 Copy", key=f"{key}_copy"):
                st.session_state.copied[garment] = st.session_state.settings[key].copy()
            if cols[1].button("📥 Paste", key=f"{key}_paste"):
                if garment in st.session_state.copied:
                    for file2 in uploaded_files:
                        k = f"{file2.name.split('.')[0]}_{garment}"
                        st.session_state.settings[k] = st.session_state.copied[garment].copy()

            if st.button(f"🔁 Refresh {garment}", key=f"{key}_refresh"):
                bg = Image.new("RGBA", (800, 1000), "white")
                box_x, box_y = 200, 300
                box_w, box_h = 400, 400
                img = Image.open(path).convert("RGBA")
                alpha = img.split()[-1]
                bbox = alpha.getbbox()
                cropped = img.crop(bbox)

                s = st.session_state.settings[key]["scale"]
                o = st.session_state.settings[key]["offset"]
                t_w = int(box_w * s / 100)
                t_h = int(box_h * s / 100)
                aspect = cropped.width / cropped.height
                new_w, new_h = (t_w, int(t_w / aspect)) if aspect > 1 else (int(t_h * aspect), t_h)
                resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
                px = box_x + (box_w - new_w) // 2
                py = box_y + (box_h - new_h) // 2 + o
                bg.paste(resized, (px, py), resized)
                st.session_state.previews[key] = bg.convert("RGB")

            if key in st.session_state.previews:
                st.image(st.session_state.previews[key], caption=f"{garment}")

if st.button("📦 Export ZIP"):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as z:
        for k, v in st.session_state.previews.items():
            img_bytes = io.BytesIO()
            v.save(img_bytes, format="JPEG")
            z.writestr(f"{k}.jpg", img_bytes.getvalue())
    st.download_button("⬇️ Download", output.getvalue(), file_name="mockups.zip", mime="application/zip")
