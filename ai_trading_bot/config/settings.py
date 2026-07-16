import os
import streamlit as st

# 🛡️ CLOUD-SMART CONFIGURATION
# This function automatically detects if we are running locally or on the web.

def get_secret(key, default_value=None):
    # 1. Check Streamlit Cloud Secrets (Priority)
    if hasattr(st, "secrets") and key in st.secrets:
        return st.secrets[key]
    
    # 2. Check System Environment (Linux Service)
    env_val = os.getenv(key)
    if env_val:
        return env_val
        
    # 3. Fallback (Local Testing)
    return default_value

# --- CREDENTIALS ---
# The app will look for "DERIV_TOKEN" in your Cloud Secrets
DERIV_TOKEN = get_secret("DERIV_TOKEN", "PLACEHOLDER_FOR_LOCAL_TESTING")
DERIV_APP_ID = get_secret("DERIV_APP_ID", "1089")

# --- TRADING RULES ---
RISK_PER_TRADE_PCT = 0.01  # Risk 1% per trade
ACCOUNT_BALANCE_FALLBACK = 10000.0
