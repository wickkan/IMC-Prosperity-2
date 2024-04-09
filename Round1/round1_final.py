import numpy as np
import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List


class Trader:

    def __init__(self):
        self.target_prices = {'STARFRUIT': 50, 'AMETHYSTS': 10000}
        self.std_dev = {
            'STARFRUIT': [11.717, 13.575, 32.751],
            'AMETHYSTS': [1.496, 1.479, 1.513]
        }

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            # Calculate acceptable price based on standard deviation and target price
            acceptable_buy_price = self.target_prices[product] - \
                self.std_dev[product][0]
            acceptable_sell_price = self.target_prices[product] + \
                self.std_dev[product][0]

            print("Acceptable buy price for",
                  product, ":", acceptable_buy_price)
            print("Acceptable sell price for",
                  product, ":", acceptable_sell_price)

            # Decide on buy orders based on the sell side of the order book
            for price, amount in order_depth.sell_orders.items():
                if price <= acceptable_buy_price:
                    print("BUY", product, "at", price, "for", amount)
                    orders.append(Order(product, price, -amount))

            # Decide on sell orders based on the buy side of the order book
            for price, amount in order_depth.buy_orders.items():
                if price >= acceptable_sell_price:
                    print("SELL", product, "at", price, "for", amount)
                    orders.append(Order(product, price, -amount))

            result[product] = orders

        # The Trader state is a simple string in this example.
        # In a full implementation, you might serialize the current Trader state
        # including any pending orders, positions, etc.
        traderData = "SAMPLE"

        # The number of conversions to make. This is a placeholder value.
        conversions = 1
        return result, conversions, traderData
