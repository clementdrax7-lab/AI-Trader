import MetaTrader5 as mt5

class MT5ExecutionEngine:
    """Manages secure order routing and position execution inside MetaTrader."""
    def __init__(self, symbol: str):
        self.symbol = symbol

    def execute_market_order(self, action_type: str, lots: float, sl: float, tp: float) -> bool:
        """Transmits direct trade requests directly to the broker execution desk."""
        if lots <= 0.0:
            print("❌ Execution rejected: Calculated position size is 0.0 lots.")
            return False

        # Map order processing constants
        order_type = mt5.ORDER_TYPE_BUY if action_type == "BUY" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(self.symbol).ask if action_type == "BUY" else mt5.symbol_info_tick(self.symbol).bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": float(lots),
            "type": order_type,
            "price": float(price),
            "sl": float(sl),
            "tp": float(tp),
            "deviation": 20, # Allowed maximum slip in points
            "magic": 123456, # Unique bot identifier
            "comment": "AI SMC Core Execution",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Ship transaction payload
        result = mt5.order_send(request)
        if result is None:
            print(f"❌ Critical: Order request timed out. Terminal error: {mt5.last_error()}")
            return False

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Order Rejected by Server! Return Code: {result.retcode} | Info: {result.comment}")
            return False

        print(f"🎯 Execution Successful! Ticket ID: {result.order} | {action_type} {lots} Lots at {price:.5f}")
        return True
