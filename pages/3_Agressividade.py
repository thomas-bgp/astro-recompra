"""Page wrapper: roda dashboard_agressividade.main() dentro do multi-page."""
import streamlit as st
st.set_page_config(page_title="Astro — Agressividade", page_icon="⚡", layout="wide")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import dashboard_agressividade as mod
mod._MULTIPAGE = True
mod.main()
