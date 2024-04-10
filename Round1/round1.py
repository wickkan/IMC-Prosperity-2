import numpy as np
import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List, Dict
import collections
from collections import defaultdict
import copy


class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([
            self.compress_state(state, ""),
            self.compress_orders(orders),
            conversions,
            "",
            "",
        ]))

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(self.to_json([
            self.compress_state(state, self.truncate(
                state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append(
                [listing["symbol"], listing["product"], listing["denomination"]])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [
                order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[:max_length - 3] + "..."


logger = Logger()


class Trader:

    def __init__(self):
        self.target_prices = {'STARFRUIT': 0, 'AMETHYSTS': 10000}
        self.position_limits = {'STARFRUIT': 20, 'AMETHYSTS': 20}
        self.std_dev = {
            'STARFRUIT': [11.717, 13.575, 32.751],
            'AMETHYSTS': [1.496, 1.479, 1.513]
        }

    def run(self, state: TradingState):
        timestamp = state.timestamp
        # Determine the phase of the trading day based on timestamp
        if timestamp <= 333330:
            time_of_day = 'early'
        elif timestamp <= 666660:
            time_of_day = 'midday'
        else:
            time_of_day = 'end_of_day'

        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            current_position = state.position.get(product, 0)
            available_buy_limit = self.position_limits[product] - \
                current_position
            available_sell_limit = self.position_limits[product] + \
                current_position

            # Calculate acceptable buy and sell prices
            if product == 'STARFRUIT':
                acceptable_buy_price, acceptable_sell_price = self.calculate_starfruit_prices(
                    time_of_day)
            else:  # For AMETHYSTS and potentially other products
                acceptable_buy_price = self.target_prices[product] - \
                    self.std_dev[product][0]
                acceptable_sell_price = self.target_prices[product] + \
                    self.std_dev[product][0]

            # Decide on buy orders based on the sell side of the order book
            for price, amount in sorted(order_depth.sell_orders.items()):
                if price <= acceptable_buy_price and available_buy_limit > 0:
                    trade_amount = min(-amount, available_buy_limit)
                    print(f"BUY {product} at {price} for {trade_amount}")
                    orders.append(Order(product, price, trade_amount))
                    available_buy_limit -= trade_amount

            # Decide on sell orders based on the buy side of the order book
            for price, amount in sorted(order_depth.buy_orders.items(), reverse=True):
                if price >= acceptable_sell_price and available_sell_limit > 0:
                    trade_amount = min(amount, available_sell_limit)
                    print(f"SELL {product} at {price} for {trade_amount}")
                    orders.append(Order(product, price, -trade_amount))
                    available_sell_limit -= trade_amount

            result[product] = orders

        traderData = "SAMPLE"  # Replace with actual trader state serialization logic
        conversions = 1  # Replace with actual conversion logic

        # Assuming logger.flush() method exists and properly implemented to handle logging.
        logger.flush(state, result, conversions, traderData)

        return result, conversions, traderData

    def calculate_starfruit_prices(self, time_of_day):
        if time_of_day == 'early':
            acceptable_buy_price = 4950
            acceptable_sell_price = 5025  # Anticipate a rise, sell early positions
        elif time_of_day == 'midday':
            acceptable_buy_price = 5030  # Prices might peak, buy on slight dips
            acceptable_sell_price = 5085  # Sell at peak prices
        else:  # end_of_day
            acceptable_buy_price = 5025  # Buy if prices dip towards the day's end
            # Anticipate a last-minute rise or prepare for the next day
            acceptable_sell_price = 5050

        return acceptable_buy_price, acceptable_sell_price
