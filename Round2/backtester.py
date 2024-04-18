import pandas as pd
from datamodel import Order, Symbol, TradingState
from trader_unfinished import Trader
from datetime import datetime
from datamodel import OrderDepth, ConversionObservation, Observation


class Backtester:
    def __init__(self, data):
        self.data = data
        self.current_index = 0

    def get_next_market_state(self):
        if self.current_index < len(self.data):
            row = self.data.iloc[self.current_index]
            self.current_index += 1
            return self.convert_row_to_trading_state(row)
        else:
            return None

    def convert_row_to_trading_state(self, row):
        # Mock the necessary structures
        # Mock timestamp if not provided
        timestamp = int(datetime.now().timestamp())
        listings = {}  # Empty, as the specific listings might not be necessary for simple backtests
        order_depths = {
            'ORCHIDS': OrderDepth()  # Assumes OrderDepth manages a dictionary of buy and sell orders
        }
        order_depths['ORCHIDS'].buy_orders = {
            row['bid_price_1']: row['bid_volume_1']}
        order_depths['ORCHIDS'].sell_orders = {
            row['ask_price_1']: row['ask_volume_1']}
        own_trades = {}
        market_trades = {}
        position = {'ORCHIDS': 0}  # Mock position, adjust based on actual data
        observations = Observation(
            plainValueObservations={},
            conversionObservations={
                'ORCHIDS': ConversionObservation(
                    bidPrice=row['bid_price_1'],
                    askPrice=row['ask_price_1'],
                    transportFees=1.5,  # Example value
                    exportTariff=0.5,   # Example value
                    importTariff=0.3,   # Example value
                    sunlight=2500,      # Example value
                    humidity=50         # Example value
                )
            }
        )

        # Create the TradingState
        state = TradingState(
            traderData='Sample trader data',
            timestamp=timestamp,
            listings=listings,
            order_depths=order_depths,
            own_trades=own_trades,
            market_trades=market_trades,
            position=position,
            observations=observations
        )
        return state


def simulate_trading():
    data = pd.read_csv(
        'Round2/Round2_DataAnalysis/backtester_data.csv', delimiter=';')
    backtester = Backtester(data)
    trader = Trader()

    total_pnl = 0

    state = backtester.get_next_market_state()
    while state is not None:
        # Run trading logic
        results, conversions, traderData = trader.run(state)

        # Here you would calculate the P&L based on trading results
        # For simplicity, we're just accumulating a dummy P&L value
        total_pnl += 0  # Adjust this to use actual results

        state = backtester.get_next_market_state()

    return total_pnl


# Call the simulation function
total_profit = simulate_trading()
print("Total Profit:", total_profit)
