from datamodel import Order, TradingState
import numpy as np


class Trader:
    def __init__(self):
        self.target_prices = {
            'STARFRUIT': 5039.5, 'AMETHYSTS': 10000, 'CHOCOLATE': 8000,
            'STRAWBERRIES': 4000, 'ROSES': 15000, 'GIFT_BASKET': 70000
        }
        self.position_limits = {
            'STARFRUIT': 20, 'AMETHYSTS': 20, 'CHOCOLATE': 250,
            'STRAWBERRIES': 350, 'ROSES': 60, 'GIFT_BASKET': 60
        }
        self.memory_length = 20
        self.price_memory = {
            product: [0] * self.memory_length for product in self.target_prices}
        # Adjust based on volatility
        self.std_dev = {product: 50 for product in self.target_prices}
        self.smoothing_factor = 0.2

    def update_price_memory(self, product, order_depth):
        best_ask = min(
            order_depth.sell_orders) if order_depth.sell_orders else None
        best_bid = max(
            order_depth.buy_orders) if order_depth.buy_orders else None
        if best_ask is not None and best_bid is not None:
            mid_price = (best_ask + best_bid) / 2
            self.price_memory[product].append(mid_price)
            if len(self.price_memory[product]) > self.memory_length:
                self.price_memory[product].pop(0)

    def predict_price_exponential_smoothing(self, product):
        prices = self.price_memory[product]
        if not prices:
            return None
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
        self.update_price_memory(product, order_depth)
        predicted_price = self.predict_price_exponential_smoothing(product)

        # Buy orders
        if best_ask and best_ask <= predicted_price - self.std_dev[product]:
            quantity = min(
                self.position_limits[product] - current_position, order_depth.sell_orders[best_ask])
            orders.append(Order(product, best_ask, quantity))
        # Sell orders
        if best_bid and best_bid >= predicted_price + self.std_dev[product]:
            quantity = min(
                current_position + self.position_limits[product], order_depth.buy_orders[best_bid])
            orders.append(Order(product, best_bid, -quantity))

        return orders

    def calc_specialty_orders(self, state, product):
        if product in ['AMETHYSTS', 'STARFRUIT'] == 'AMETHYSTS':
            return self.calc_amethysts_orders(state, product)
        else:
            return self.calc_starfruit_orders(state, product)

    def calc_amethysts_orders(self, state, product="AMETHYSTS"):
        order_depth = state.order_depths[product]
        orders = []
        current_position = state.position.get(product, 0)
        available_buy_limit = self.position_limits[product] - current_position
        available_sell_limit = self.position_limits[product] + current_position

        acceptable_buy_price = self.target_prices[product] - \
            self.std_dev[product]
        acceptable_sell_price = self.target_prices[product] + \
            self.std_dev[product]

        print("Acceptable buy price for", product, ":", acceptable_buy_price)
        print("Acceptable sell price for", product, ":", acceptable_sell_price)

        # Decide on buy orders based on the sell side of the order book
        for price, amount in sorted(order_depth.sell_orders.items()):
            if price <= acceptable_buy_price:
                trade_amount = min(-amount, available_buy_limit)
                if trade_amount > 0:
                    print("BUY", product, "at", price, "for", trade_amount)
                    orders.append(Order(product, price, trade_amount))
                    available_buy_limit -= trade_amount

        # Decide on sell orders based on the buy side of the order book
        for price, amount in sorted(order_depth.buy_orders.items(), reverse=True):
            if price >= acceptable_sell_price:
                trade_amount = min(amount, available_sell_limit)
                if trade_amount > 0:
                    print("SELL", product, "at", price, "for", trade_amount)
                    orders.append(Order(product, price, -trade_amount))
                    available_sell_limit -= trade_amount

        return orders

    def calc_starfruit_orders(self, state, product="STARFRUIT"):
        order_depth = state.order_depths[product]
        self.update_price_memory(product, order_depth)
        predicted_price = self.predict_price_exponential_smoothing(product)
        if predicted_price is None:
            return []

        orders = []
        current_position = state.position.get(product, 0)
        available_buy_limit = self.position_limits[product] - current_position
        available_sell_limit = self.position_limits[product] + current_position

        # Buy orders
        for price, amount in sorted(order_depth.sell_orders.items()):
            if price <= predicted_price:
                trade_amount = min(-amount, available_buy_limit)
                if trade_amount > 0:
                    orders.append(Order(product, price, trade_amount))
                    available_buy_limit -= trade_amount

        # Sell orders
        for price, amount in sorted(order_depth.buy_orders.items(), reverse=True):
            if price >= predicted_price:
                trade_amount = min(amount, available_sell_limit)
                if trade_amount > 0:
                    orders.append(Order(product, price, -trade_amount))
                    available_sell_limit -= trade_amount

        return orders

    def calc_roses_orders(self, state, product="ROSES"):
        order_depth = state.order_depths[product]
        best_ask = min(
            order_depth.sell_orders) if order_depth.sell_orders else None
        best_bid = max(
            order_depth.buy_orders) if order_depth.buy_orders else None

        # Update price memory and calculate the moving average
        self.update_price_memory(product, order_depth)
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
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        result["AMETHYSTS"] = self.calc_amethysts_orders(state)
        result["STARFRUIT"] = self.calc_starfruit_orders(state)
        result["GIFT_BASKET"] = self.calc_orders_for_product(
            state, "GIFT_BASKET")
        result["CHOCOLATE"] = self.calc_orders_for_product(state, "CHOCOLATE")
        result["ROSES"] = self.calc_roses_orders(state)
        result["STRAWBERRIES"] = self.calc_orders_for_product(
            state, "STRAWBERRIES")

        traderData = "SAMPLE"  # Replace with actual trader state serialization logic
        conversions = 1  # Replace with actual conversion logic
        # Make sure to pass the correct orders structure to the logger
        return result, conversions, traderData
