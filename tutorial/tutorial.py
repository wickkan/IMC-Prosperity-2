import numpy as np
import json
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import Any


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
        self.logger = Logger()  # Instantiate the Logger
        self.position_limits = {"AMETHYSTS": 20, "STARFRUIT": 20}
        self.position = {"AMETHYSTS": 0, "STARFRUIT": 0}
        self.price_memory = {"AMETHYSTS": [], "STARFRUIT": []}
        self.stop_loss_threshold = {"AMETHYSTS": -
                                    10, "STARFRUIT": -10}  # Example values
        self.profit_target = {"AMETHYSTS": 10,
                              "STARFRUIT": 10}  # Example values

    def update_price_memory(self, product, order_depth):
        best_ask = min(
            order_depth.sell_orders) if order_depth.sell_orders else None
        best_bid = max(
            order_depth.buy_orders) if order_depth.buy_orders else None
        if best_ask and best_bid:
            mid_price = (best_ask + best_bid) / 2
            self.price_memory[product].append(mid_price)

    def calculate_acceptable_price(self, product):
        if self.price_memory[product]:
            recent_prices = self.price_memory[product][-5:]
            avg_price = sum(recent_prices) / len(recent_prices)
            price_variance = np.var(recent_prices)
            if price_variance > 1:
                # Adapt prices based on volatility
                return avg_price * (1 + np.sign(price_variance - 1) * 0.05)
            return avg_price
        return None

    def decide_order_for_product(self, product, order_depth):
        orders = []
        self.update_price_memory(product, order_depth)
        acceptable_price = self.calculate_acceptable_price(product)
        if not acceptable_price:
            return orders

        current_position = self.position[product]
        stop_loss_price = acceptable_price + self.stop_loss_threshold[product]
        profit_target_price = acceptable_price + self.profit_target[product]

        for ask, qty in order_depth.sell_orders.items():
            if ask < acceptable_price and current_position < self.position_limits[product]:
                order_qty = min(-qty,
                                self.position_limits[product] - current_position)
                if self.check_stop_loss(current_position, ask, stop_loss_price):
                    orders.append(Order(product, ask, order_qty))
                    self.position[product] += order_qty

        for bid, qty in order_depth.buy_orders.items():
            if bid > acceptable_price and current_position > -self.position_limits[product]:
                order_qty = -min(qty, current_position +
                                 self.position_limits[product])
                if self.check_profit_target(current_position, bid, profit_target_price):
                    orders.append(Order(product, bid, order_qty))
                    self.position[product] += order_qty

        return orders

    def check_stop_loss(self, position, current_price, stop_loss_price):
        return position > 0 or current_price > stop_loss_price

    def check_profit_target(self, position, current_price, profit_target_price):
        return position < 0 or current_price < profit_target_price

    def run(self, state: TradingState):
        self.logger.print("traderData: " + state.traderData)
        self.logger.print("Observations: " + str(state.observations))
        result = {}

        for product in state.order_depths:
            order_depth = state.order_depths[product]
            orders = self.decide_order_for_product(product, order_depth)
            result[product] = orders

        traderData = "Adaptive Strategy Based on Market Conditions"
        conversions = 1

        # Use logger to flush final output instead of returning it directly
        self.logger.flush(state, result, conversions, traderData)

        # Optionally, you can still return the result, conversions, and traderData if needed by other parts of your program
        return result, conversions, traderData
