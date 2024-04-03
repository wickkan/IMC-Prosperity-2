from datamodel import TradingState, OrderDepth, Order, Listing
# Add Tuple and Dict to your imports
from typing import List, Tuple, Dict
# Import any other necessary classes or modules


class Trader:

    def __init__(self):
        # Example thresholds, these should be adjusted based on your strategy and observations
        self.amethysts_buy_price = 8
        self.amethysts_sell_price = 12
        self.starfruit_buy_price = 10
        self.starfruit_sell_price = 15
        # To track STARFRUIT price history for trend analysis
        self.starfruit_price_history = []

    def update_price_history(self, product: str, mid_price: float):
        if product == "STARFRUIT":
            self.starfruit_price_history.append(mid_price)
            if len(self.starfruit_price_history) > 10:
                self.starfruit_price_history.pop(0)

    def analyze_starfruit_trend(self):
        if len(self.starfruit_price_history) >= 5:
            recent_avg = sum(self.starfruit_price_history[-5:]) / 5
            overall_avg = sum(self.starfruit_price_history) / \
                len(self.starfruit_price_history)
            if recent_avg > overall_avg:
                self.starfruit_buy_price = min(
                    self.starfruit_buy_price * 1.05, self.starfruit_sell_price - 0.01)
            else:
                self.starfruit_sell_price = max(
                    self.starfruit_sell_price * 0.95, self.starfruit_buy_price + 0.01)

    def adjust_starfruit_prices(self, order_depth: OrderDepth):
        best_ask, best_ask_qty = self.get_best_ask(order_depth)
        best_bid, best_bid_qty = self.get_best_bid(order_depth)
        if best_ask and best_bid:
            mid_price = (best_ask + best_bid) / 2
            self.update_price_history("STARFRUIT", mid_price)
            self.analyze_starfruit_trend()

    def decide_order_for_product(self, product: str, order_depth: OrderDepth, current_position: int) -> List[Order]:
        """
        Decide on the orders to place for a given product based on its market depth and current position.
        """
        orders = []

        # Simple strategy for AMETHYSTS
        if product == "AMETHYSTS":
            best_ask, best_ask_amount = self.get_best_ask(order_depth)
            if best_ask and best_ask <= self.amethysts_buy_price and current_position < 20:
                quantity = min(-best_ask_amount, 20 - current_position)
                orders.append(Order(product, best_ask, quantity))

            best_bid, best_bid_amount = self.get_best_bid(order_depth)
            if best_bid and best_bid >= self.amethysts_sell_price and current_position > 0:
                quantity = min(best_bid_amount, current_position)
                orders.append(Order(product, best_bid, -quantity))

        # Dynamic strategy for STARFRUIT, simplified for this example
        elif product == "STARFRUIT":
            self.adjust_starfruit_prices(order_depth)
            print(f"Adjusted STARFRUIT Prices: Buy at {
                  self.starfruit_buy_price}, Sell at {self.starfruit_sell_price}")
            best_ask, best_ask_qty = self.get_best_ask(order_depth)
            print(f"Evaluating STARFRUIT: best ask {
                  best_ask} with quantity {best_ask_qty}")
            if best_ask <= self.starfruit_buy_price and current_position < 20:
                # Adjusting buy quantity to be positive
                quantity = min(best_ask_qty, 20 - current_position)
                print(f"Placing BUY order for STARFRUIT: {
                      quantity} at {best_ask}")
                orders.append(Order(product, best_ask, quantity))

            best_bid, best_bid_qty = self.get_best_bid(order_depth)
            if best_bid >= self.starfruit_sell_price and current_position > 0:
                # Adjusting sell quantity to be negative
                quantity = -min(best_bid_qty, current_position)
                orders.append(Order(product, best_bid, quantity))

        return orders

    def get_best_ask(self, order_depth: OrderDepth) -> Tuple[int, int]:
        if order_depth.sell_orders:
            return sorted(order_depth.sell_orders.items())[0]
        return None, None

    def get_best_bid(self, order_depth: OrderDepth) -> Tuple[int, int]:
        if order_depth.buy_orders:
            return sorted(order_depth.buy_orders.items(), reverse=True)[0]
        return None, None

    def run(self, state: TradingState):
        print("traderData: ", state.traderData)
        print("Observations: ", state.observations)
        result = {}

        for product, order_depth in state.order_depths.items():
            # Dynamic strategy for STARFRUIT prices
            if product == "STARFRUIT":
                self.adjust_starfruit_prices(order_depth)

            orders = self.decide_order_for_product(
                product, order_depth, state.position.get(product, 0))
            result[product] = orders

        # Reflects adjustments for dynamic strategy
        traderData = "Dynamic Strategy Data"
        conversions = 1  # Placeholder for conversions logic; adjust as per your strategy needs

        return result, conversions, traderData
