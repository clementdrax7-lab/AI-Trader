class RiskManager:

    def calculate(self, balance, risk_percent, stop_loss_points, reward_ratio):

        risk_amount = balance * (risk_percent / 100)

        take_profit_points = (
            stop_loss_points * reward_ratio
        )

        return {
            "risk_allowed": risk_percent <= 2,
            "risk_amount": risk_amount,
            "stop_loss": stop_loss_points,
            "take_profit": take_profit_points,
            "risk_reward": reward_ratio
        }
