"""Page wrapper: roda dashboard_recompra.main() dentro do multi-page."""
import streamlit as st
st.set_page_config(page_title="Astro — Recompra", page_icon="📊", layout="wide")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and run — skip the set_page_config inside
import dashboard_recompra as mod
mod._MULTIPAGE = True
mod.main()
