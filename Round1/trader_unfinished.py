import numpy as np
import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List, Dict
import numpy as np


class Trader:

    def __init__(self):
        self.target_prices = {'STARFRUIT': 5068, 'AMETHYSTS': 10000}
        self.position_limits = {'STARFRUIT': 20, 'AMETHYSTS': 20}
        self.std_dev = {
            'STARFRUIT': [11.717, 13.575, 32.751],
            'AMETHYSTS': [1.496, 1.479, 1.513]
        }

    def run(self, state: TradingState):
        # need to update initial starfruit price based on order depth
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            current_position = state.position.get(product, 0)
            available_buy_limit = self.position_limits[product] - \
                current_position
            available_sell_limit = self.position_limits[product] + \
                current_position

            acceptable_buy_price = self.target_prices[product] - \
                self.std_dev[product][0]
            acceptable_sell_price = self.target_prices[product] + \
                self.std_dev[product][0]

            print("Acceptable buy price for",
                  product, ":", acceptable_buy_price)
            print("Acceptable sell price for",
                  product, ":", acceptable_sell_price)

            # Decide on buy orders based on the sell side of the order book
            for price, amount in sorted(order_depth.sell_orders.items()):
                if price <= acceptable_buy_price:
                    trade_amount = min(-amount, available_buy_limit)
                    if trade_amount > 0:
                        print("BUY", product, "at", price, "for", trade_amount)
                        orders.append(Order(product, price, trade_amount))
                        available_buy_limit -= trade_amount
                        if product == "STARFRUIT":
                            self.position_limits[product] = price

            # Decide on sell orders based on the buy side of the order book
            for price, amount in sorted(order_depth.buy_orders.items(), reverse=True):
                if price >= acceptable_sell_price:
                    trade_amount = min(amount, available_sell_limit)
                    if trade_amount > 0:
                        print("SELL", product, "at",
                              price, "for", trade_amount)
                        orders.append(Order(product, price, -trade_amount))
                        available_sell_limit -= trade_amount
                        if product == "STARFRUIT":
                            self.position_limits[product] = price

            result[product] = orders

        traderData = "SAMPLE"  # Replace with actual trader state serialization logic
        conversions = 1  # Replace with actual conversion logic
        return result, conversions, traderData
