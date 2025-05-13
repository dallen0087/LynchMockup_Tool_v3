
import streamlit as st
from PIL import Image
import numpy as np
import os

# Minimal stable manual-refresh logic for demo

garments = {
    "tshirts": {"preview": "WHITE", "colors": ["WHITE"], "dark_colors": []},
}

st.title("LynchMockup_Tool v5 — Manual Refresh")

uploaded_files = st.file_uploader("Upload PNG designs", type=["png"], accept_multiple_files=True)

if "settings" not in st.session_state:
    st.session_state.settings = {}
if "previews" not in st.session_state:
    st.session_state.previews = {}
if "refresh_flags" not in st.session_state:
    st.session_state.refresh_flags = {}

if uploaded_files:
    os.makedirs("temp_designs", exist_ok=True)

    for uploaded_file in uploaded_files:
        design_name = uploaded_file.name.split('.')[0]
        path = f"temp_designs/{design_name}.png"
        with open(path, "wb") as f:
            f.write(uploaded_file.getvalue())
        image = Image.open(path).convert("RGBA")

        st.header(f"Design: {design_name}")
        for garment, config in garments.items():
            key = f"{design_name}_{garment}"
            if key not in st.session_state.settings:
                st.session_state.settings[key] = {"scale": 100, "offset": 0}
            if key not in st.session_state.refresh_flags:
                st.session_state.refresh_flags[key] = False

            scale = st.slider("Scale", 50, 100, st.session_state.settings[key]["scale"], key=f"{key}_scale")
            offset = st.slider("Offset", -100, 100, st.session_state.settings[key]["offset"], key=f"{key}_offset")
            st.session_state.settings[key]["scale"] = scale
            st.session_state.settings[key]["offset"] = offset

            if st.button(f"🔁 Refresh {garment}", key=f"{key}_refresh"):
                st.session_state.refresh_flags[key] = True

            if st.session_state.refresh_flags[key]:
                bg = Image.new("RGBA", (800, 1000), "white")
                box_w, box_h = 400, 400
                target_w = int(box_w * (scale / 100))
                target_h = int(box_h * (scale / 100))
                aspect = image.width / image.height
                if aspect > 1:
                    new_w = target_w
                    new_h = int(new_w / aspect)
                else:
                    new_h = target_h
                    new_w = int(new_h * aspect)
                resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                px = 200 + (box_w - new_w) // 2
                py = 300 + (box_h - new_h) // 2 + offset
                bg.paste(resized, (px, py), resized)
                st.session_state.previews[key] = bg.convert("RGB")
                st.session_state.refresh_flags[key] = False

            if key in st.session_state.previews:
                st.image(st.session_state.previews[key], caption=f"{garment} preview")
