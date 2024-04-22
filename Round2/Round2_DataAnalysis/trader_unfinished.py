from datamodel import OrderDepth, UserId, TradingState, Order, ConversionObservation, Observation
from typing import List, Dict
import numpy as np
import pandas as pd
import logging
from typing import Dict, List


# Load the data
prices_day_minus_1 = pd.read_csv(
    '/Users/kanishkaw/Desktop/Tech/IMC-Prosperity2/Round2/Round2_DataAnalysis/prices_round_2_day_-1.csv', delimiter=';')
prices_day_0 = pd.read_csv(
    '/Users/kanishkaw/Desktop/Tech/IMC-Prosperity2/Round2/Round2_DataAnalysis/prices_round_2_day_0.csv', delimiter=';')
prices_day_1 = pd.read_csv(
    '/Users/kanishkaw/Desktop/Tech/IMC-Prosperity2/Round2/Round2_DataAnalysis/prices_round_2_day_1.csv', delimiter=';')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class ConversionObservation:
    def __init__(self, bidPrice: float, askPrice: float, transportFees: float, exportTariff: float, importTariff: float, sunlight: float, humidity: float):
        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.transportFees = transportFees
        self.exportTariff = exportTariff
        self.importTariff = importTariff
        self.sunlight = sunlight
        self.humidity = humidity


class Order:
    def __init__(self, symbol: str, price: float, quantity: int):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity


class OrderDepth:
    def __init__(self):
        self.buy_orders: Dict[float, int] = {}
        self.sell_orders: Dict[float, int] = {}


class Observation:
    def __init__(self, plainValueObservations: Dict[str, int], conversionObservations: Dict[str, ConversionObservation]):
        self.plainValueObservations = plainValueObservations
        self.conversionObservations = conversionObservations

    def __str__(self):
        # This method returns a string representation of the observation details.
        conversion_details = {k: v.__dict__ for k,
                              v in self.conversionObservations.items()}
        return f"Plain Values: {self.plainValueObservations}, Conversion Details: {conversion_details}"


class TradingState:
    def __init__(self, traderData: str, timestamp: int, listings: Dict[str, str], order_depths: Dict[str, OrderDepth], own_trades: Dict[str, List[Order]], market_trades: Dict[str, List[Order]], position: Dict[str, int], observations: Observation):
        self.traderData = traderData
        self.timestamp = timestamp
        self.listings = listings
        self.order_depths = order_depths
        self.own_trades = own_trades
        self.market_trades = market_trades
        self.position = position
        self.observations = observations


class Trader:
    def __init__(self):
        self.target_prices = {'ORCHIDS': 1200}
        self.position_limits = {'ORCHIDS': 100}
        self.price_memory = {'ORCHIDS': []}
        self.memory_length = 20
        self.smoothing_factor = 0.2
        self.sunlight_threshold = 2500 * 7
        self.humidity_optimal_range = (60, 80)

    def update_price_memory(self, product, price):
        self.price_memory[product].append(price)
        if len(self.price_memory[product]) > self.memory_length:
            self.price_memory[product].pop(0)

    def predict_price(self, product):
        prices = self.price_memory[product]
        if not prices:
            return None
        smooth_price = prices[0]
        for price in prices[1:]:
            smooth_price = self.smoothing_factor * price + \
                (1 - self.smoothing_factor) * smooth_price
        return smooth_price

    def run(self, state: TradingState):
        logging.debug("traderData: %s", state.traderData)
        logging.debug("Observations: %s", state.observations)
        result = {}
        conversions = 0

        for product, order_depth in state.order_depths.items():
            if product == 'ORCHIDS':
                orders = self.trade_orchids(state, product, order_depth)
                result[product] = orders
        traderData = "Updated state information"
        return result, conversions, traderData

    def trade_orchids(self, state, product, order_depth):
        conversion_observation = state.observations.conversionObservations.get(
            product)
        sunlight = conversion_observation.sunlight if conversion_observation else 0
        humidity = conversion_observation.humidity if conversion_observation else 0

        price_adjustment = self.calculate_environmental_impact(
            sunlight, humidity)
        target_price = self.target_prices[product] + price_adjustment

        best_ask = min(order_depth.sell_orders, default=None)
        best_bid = max(order_depth.buy_orders, default=None)
        self.update_price_memory(
            product, (best_ask + best_bid) / 2 if best_ask and best_bid else 0)
        predicted_price = self.predict_price(product)

        orders = []
        if best_ask and best_ask < target_price:
            quantity = min(
                self.position_limits[product], order_depth.sell_orders[best_ask])
            orders.append(Order(product, best_ask, quantity))
        if best_bid and best_bid > target_price:
            quantity = min(
                self.position_limits[product], order_depth.buy_orders[best_bid])
            orders.append(Order(product, best_bid, -quantity))
        return orders

    def calculate_environmental_impact(self, sunlight, humidity):
        price_adjustment = 0
        if sunlight < self.sunlight_threshold:
            price_adjustment -= 4 * \
                ((self.sunlight_threshold - sunlight) / (2500 * 10))
        if humidity < self.humidity_optimal_range[0] or humidity > self.humidity_optimal_range[1]:
            deviation = min(abs(humidity - self.humidity_optimal_range[0]), abs(
                humidity - self.humidity_optimal_range[1]))
            price_adjustment -= 2 * (deviation / 5)
        return price_adjustment


trader = Trader()  # Re-instantiate the trader with the corrected class definitions

trading_results = []
for index, row in prices_day_minus_1.iterrows():
    order_depth = OrderDepth()
    order_depth.buy_orders = {row['ORCHIDS'] - 1: 10}  # Example order depth
    order_depth.sell_orders = {row['ORCHIDS'] + 1: 10}  # Example order depth

    conversion_observation = ConversionObservation(
        bidPrice=row['ORCHIDS'] - 1,
        askPrice=row['ORCHIDS'] + 1,
        transportFees=row['TRANSPORT_FEES'],
        exportTariff=row['EXPORT_TARIFF'],
        importTariff=row['IMPORT_TARIFF'],
        sunlight=row['SUNLIGHT'],
        humidity=row['HUMIDITY']
    )
    observation = Observation(
        plainValueObservations={},
        conversionObservations={'ORCHIDS': conversion_observation}
    )
    state = TradingState(
        traderData="",
        timestamp=row['timestamp'],
        listings={},
        order_depths={'ORCHIDS': order_depth},
        own_trades={},
        market_trades={},
        position={},
        observations=observation
    )

    result, conversions, traderData = trader.run(state)
    trading_results.append((index, result, conversions, traderData))
    results_df = pd.DataFrame(trading_results)
    results_df.columns = ['timestamp', 'orders', 'conversions', 'traderData']
    print(results_df)
