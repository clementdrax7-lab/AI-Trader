class AdvancedRiskManager:
    """Calculates risk parameters and lot sizing for Linux/Deriv systems."""
    def __init__(self, account_risk_pct: float = 0.01, max_daily_loss_pct: float = 0.03):
        self.risk_pct = account_risk_pct
        self.max_daily_loss_pct = max_daily_loss_pct

    def calculate_position_size(self, symbol: str, entry: float, stop_loss: float) -> float:
        """Calculates position volume sizing based on risk parameters."""
        # Distance between your execution entry and technical stop loss structural levels
        risk_distance = abs(entry - stop_loss)
        if risk_distance == 0:
            return 0.1 # Safe default baseline micro-lot size split

        # Base mock balance of $10,000 for calculation metrics on local test environments
        mock_balance = 10000.0
        risk_amount = mock_balance * self.risk_pct
        
        # Calculate raw lot configurations based on standard synthetic point steps
        raw_lot_size = risk_amount / (risk_distance * 100)
        
        # Keep trade volume normalized safely between 0.10 and 10.0 contracts
        return max(0.1, min(round(raw_lot_size, 2), 10.0))
