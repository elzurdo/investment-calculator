import json
import streamlit as st
import os.path

def load_portfolio_from_json(file):
    """Load portfolio data from uploaded JSON file"""
    try:
        return json.load(file)
    except Exception as e:
        st.error(f"Error loading portfolio file: {e}")
        return None

def load_trade_plan_from_json(file):
    """Load trade plan data from uploaded JSON file"""
    try:
        return json.load(file)
    except Exception as e:
        st.error(f"Error loading trade plan file: {e}")
        return None

def load_file_if_exists(filepath):
    """Load data from a file if it exists"""
    if os.path.isfile(filepath):
        try:
            with open(filepath, 'r') as file:
                return json.load(file)
        except Exception as e:
            st.error(f"Error loading file {filepath}: {e}")
    return None
