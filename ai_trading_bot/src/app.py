import streamlit as st
import asyncio
import json
import websockets

st.set_page_config(page_title="Connection Doctor", page_icon="🩺")

st.markdown("""
    <style>
        .stApp { background-color: #111; color: white; }
        .box { padding: 20px; border-radius: 10px; background: #222; border: 1px solid #444; }
    </style>
""", unsafe_allow_html=True)

st.title("🩺 Sniper Connection Doctor")

# 1. Get Token (Clean it)
raw_token = st.secrets.get("DERIV_TOKEN", "")
token = raw_token.strip().replace('"', '').replace("'", "")

st.markdown(f"<div class='box'><h3>🔑 Key Inspector</h3><p>Length: <b>{len(token)}</b> characters</p><p>First 2 chars: <b>{token[:2]}***</b></p><p>Last 2 chars: <b>***{token[-2:]}</b></p></div>", unsafe_allow_html=True)

async def test_connection():
    uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(uri) as websocket:
        # Step 1: Authorize
        st.write("---")
        st.info("📡 Dialing Deriv Server...")
        await websocket.send(json.dumps({"authorize": token}))
        response = await websocket.recv()
        data = json.loads(response)
        
        if 'error' in data:
            err = data['error']
            st.error(f"❌ REJECTED: {err['code']}")
            st.error(f"Message: {err['message']}")
            
            if err['code'] == 'InvalidToken':
                st.warning("👉 DIAGNOSIS: The token characters are wrong. Check for typos.")
            elif err['code'] == 'InputValidationFailed':
                st.warning("👉 DIAGNOSIS: You have hidden spaces or invalid characters (like emoji or quotes) inside the key.")
        else:
            st.success("✅ APPROVED! KEY IS WORKING")
            account = data['authorize']
            st.markdown(f"""
                <div class='box' style='border-color: #00FF00;'>
                    <h2>✅ ACCOUNT LINKED</h2>
                    <p><b>User:</b> {account['email']}</p>
                    <p><b>Account ID:</b> {account['loginid']}</p>
                    <p><b>Balance:</b> {account['balance']} {account['currency']}</p>
                    <p><b>Demo/Real:</b> {'DEMO' if account['is_virtual'] else 'REAL'}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if "trade" not in account['scopes']:
                st.error("⛔ ISSUE: Key works, but lacks 'Trade' permission.")
            else:
                st.balloons()
                st.success("🚀 READY TO DEPLOY: You can switch back to V28 code now.")

if st.button("RUN DIAGNOSIS NOW"):
    if len(token) < 5:
        st.error("⚠️ Secrets Empty or Invalid format.")
    else:
        asyncio.run(test_connection())
