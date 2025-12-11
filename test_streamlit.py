
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
print('Python path:', sys.path[:3])

try:
    from src.dashboard.components.strategy_optimizer import render_strategy_optimizer
    st.success('Strategy optimizer imported successfully')
except Exception as e:
    st.error(f'Import failed: {e}')
    st.code(str(e))

