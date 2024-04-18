import json
from datamodel import TradingState, OrderDepth, Trade, Listing, Order, ConversionObservation, Observation
from typing import List, Dict


class Trader:

    def run(self, state: TradingState):
        print("traderData: ", state.traderData)
        print("Observations: ", str(state.observations))

        orchid_obs = state.observations.conversionObservations.get('ORCHIDS')
        local_market_price = self.calculate_acceptable_price(
            orchid_obs.sunlight, orchid_obs.humidity)

        result = {}
        current_position = state.position.get('ORCHIDS', 0)
        conversions = 0

        order_depth = state.order_depths.get('ORCHIDS', OrderDepth())
        local_best_ask = min(order_depth.sell_orders, default=float('inf'))
        local_best_bid = max(order_depth.buy_orders, default=0)

        # Market making strategy: place buy and sell orders around the mid-price
        mid_price = (local_best_ask + local_best_bid) / \
            2 if local_best_bid > 0 else local_market_price
        # Buy at 95% of mid-price, rounded to nearest integer
        buy_price = int(mid_price * 0.95)
        # Sell at 105% of mid-price, rounded to nearest integer
        sell_price = int(mid_price * 1.05)

        # Check if buying or selling is feasible
        if buy_price < local_best_ask:
            # Don't exceed position limits
            quantity = min(100 - current_position, 10)
            result['ORCHIDS'] = [Order('ORCHIDS', buy_price, quantity)]

        if sell_price > local_best_bid and current_position > 0:
            # Sell only if we have inventory
            quantity = min(current_position, 10)
            result['ORCHIDS'] = [Order('ORCHIDS', sell_price, -quantity)]

        traderData = "Updated Trader Data"
        return result, conversions, traderData

    def calculate_acceptable_price(self, sunlight: float, humidity: float) -> float:
        # Simplified environmental adjustment
        base_price = 1000 + (sunlight - 2500) / 50 - \
            ((humidity - 70) ** 2) / 100
        return int(base_price)  # Ensure the price is an integer
