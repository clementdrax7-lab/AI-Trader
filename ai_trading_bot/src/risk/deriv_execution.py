import json
import asyncio
import websockets
from ai_trading_bot.config.settings import DERIV_TOKEN, DERIV_APP_ID


class DerivExecutionEngine:
    """Executes live authenticated trade transactions on your real or demo Deriv account."""
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ws_url = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"

    async def transmit_order(self, action_type: str, lots: float, sl: float, tp: float) -> bool:
        if lots <= 0.0:
            return False

        # Translate direction names into standard contract structures
        contract_type = "CALL" if action_type == "BUY" else "PUT"
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Gate 1: Secure Account Handshake Authentication
                auth_payload = {"authorize": DERIV_TOKEN}
                await websocket.send(json.dumps(auth_payload))
                auth_resp = json.loads(await websocket.recv())
                
                if "error" in auth_resp:
                    print(f"❌ [AUTH FAILED] Secure token rejected by Deriv: {auth_resp['error']['message']}")
                    return False
                
                print(f"🔒 Authenticated successfully. Account Owner: {auth_resp['authorize']['email']}")
                
                # Gate 2: Route Trade Contract Request Parameters
                trade_payload = {
                    "buy": 1,
                    "price": 10.0, # Target default stake amount value
                    "parameters": {
                        "amount": float(lots * 10),
                        "basis": "stake",
                        "contract_type": contract_type,
                        "currency": "USD",
                        "duration": 15,
                        "duration_unit": "m", # Matches 15-Minute chart parameters
                        "symbol": self.symbol,
                        "barrier": f"+0.05" if contract_type == "CALL" else "-0.05"
                    }
                }
                
                await websocket.send(json.dumps(trade_payload))
                trade_resp = json.loads(await websocket.recv())
                
                if "error" in trade_resp:
                    print(f"❌ [ORDER REJECTED] Platform declined contract parameters: {trade_resp['error']['message']}")
                    return False
                
                contract_id = trade_resp["buy"]["contract_id"]
                print(f"🎯 [LIVE EXECUTION SUCCESSFUL] Transaction recorded! Contract ID Reference: {contract_id}")
                return True
                
        except Exception as e:
            print(f"❌ [CRITICAL TRANSACTION EXCEPTION] Network failure encountered during routing: {e}")
            return False

    def execute_market_order(self, action_type: str, lots: float, sl: float, tp: float) -> bool:
        """Bridges synchronous execution frameworks with the authenticated network data stack."""
        return asyncio.run(self.transmit_order(action_type, lots, sl, tp))
