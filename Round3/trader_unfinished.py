import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any, List
import numpy as np


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
        # Set initial target prices based on expected market values or previous analysis
        self.target_prices = {
            'CHOCOLATE': 8000, 'STRAWBERRIES': 4000, 'ROSES': 15000, 'GIFT_BASKET': 70000}
        self.position_limits = {
            'CHOCOLATE': 250, 'STRAWBERRIES': 350, 'ROSES': 60, 'GIFT_BASKET': 60}
        self.memory_length = 20
        self.price_memory = {
            product: [0] * self.memory_length for product in self.target_prices}
        # This might need adjustment based on volatility analysis
        self.std_dev = {product: 50 for product in self.target_prices}
        self.smoothing_factor = 0.2

    def update_price_memory(self, product, best_ask, best_bid):
        if best_ask is not None and best_bid is not None:
            mid_price = (best_ask + best_bid) / 2
            self.price_memory[product].append(mid_price)
            if len(self.price_memory[product]) > self.memory_length:
                self.price_memory[product].pop(0)

    def predict_price_exponential_smoothing(self, product):
        prices = self.price_memory[product]
        smooth_price = prices[0]
        for price in prices[1:]:
            smooth_price = self.smoothing_factor * price + \
                (1 - self.smoothing_factor) * smooth_price
        return smooth_price

    def calculate_trading_limits(self, product, current_position, price, direction):
        if direction == 'buy':
            available_limit = self.position_limits[product] - current_position
            acceptable_price = self.target_prices[product] - \
                self.std_dev[product]
            return price <= acceptable_price, min(available_limit, int(self.position_limits[product] / price))
        else:
            available_limit = self.position_limits[product] + current_position
            acceptable_price = self.target_prices[product] + \
                self.std_dev[product]
            return price >= acceptable_price, available_limit

    def calc_orders_for_product(self, state, product):
        orders = []
        order_depth = state.order_depths[product]
        best_ask = min(
            order_depth.sell_orders) if order_depth.sell_orders else None
        best_bid = max(
            order_depth.buy_orders) if order_depth.buy_orders else None
        current_position = state.position.get(product, 0)

        self.update_price_memory(product, best_ask, best_bid)
        predicted_price = self.predict_price_exponential_smoothing(product)
        # Buy orders
        if best_ask is not None:
            buy_condition, buy_amount = self.calculate_trading_limits(
                product, current_position, best_ask, 'buy')
            if buy_condition:
                orders.append(Order(product, best_ask, buy_amount))
        # Sell orders
        if best_bid is not None:
            sell_condition, sell_amount = self.calculate_trading_limits(
                product, current_position, best_bid, 'sell')
            if sell_condition:
                orders.append(Order(product, best_bid, -sell_amount))

        return orders

    def calc_roses_orders(self, state, product="ROSES"):
        order_depth = state.order_depths[product]
        best_ask = min(
            order_depth.sell_orders) if order_depth.sell_orders else None
        best_bid = max(
            order_depth.buy_orders) if order_depth.buy_orders else None

        # Update price memory and calculate the moving average
        self.update_price_memory(product, best_ask, best_bid)
        # last 10 prices for the moving average
        moving_avg = np.mean(self.price_memory[product][-10:])

        orders = []
        if best_ask and best_ask < moving_avg * 0.98:  # Buy if the price is 2% below the moving average
            orders.append(Order(product, best_ask, min(
                self.position_limits[product], order_depth.sell_orders[best_ask])))
        if best_bid and best_bid > moving_avg * 1.02:  # Sell if the price is 2% above the moving average
            orders.append(Order(product, best_bid, -
                                min(self.position_limits[product], order_depth.buy_orders[best_bid])))

        return orders

    def run(self, state: TradingState):
        result = {}

        for product in ['CHOCOLATE', 'STRAWBERRIES', 'ROSES', 'GIFT_BASKET']:
            if product == 'ROSES':  # Special handling for ROSES
                result[product] = self.calc_roses_orders(state, product)
            else:
                result[product] = self.calc_orders_for_product(
                    state, product)

        # Update with actual state data if necessary
        traderData = "State info for next round"
        conversions = 1  # Update conversion logic if applicable

        # Ensure all data is logged before returning
        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData
