# IMC-Prosperity2

Tutorial:

This Python class `Trader` represents a trading algorithm for a simulated market environment. It manages trades for two products, `AMETHYSTS` and `STARFRUIT`, with the aim of making profitable transactions based on the market conditions.

**Class Initialization:**
- Sets position limits for each product, indicating the maximum number of units that can be held at any time.
- Initializes the current position for each product, tracking how many units are currently held.
- Maintains a price memory for each product to store recent transaction prices.
- Defines stop-loss thresholds and profit targets for each product to manage risk.

**Key Methods:**
- `update_price_memory()`: Updates the price memory with the latest mid-price calculated from the best available buy (bid) and sell (ask) prices.
- `calculate_acceptable_price()`: Calculates an average price based on recent prices and adjusts it based on the observed price variance.
- `decide_order_for_product()`: Determines buy or sell orders for a product. It ensures trades don't exceed position limits and checks against stop-loss and profit target conditions before placing an order.
- `check_stop_loss()`: Checks if the stop-loss condition is triggered, to prevent further loss.
- `check_profit_target()`: Checks if the profit target is met, to realize gains.

**Main Execution - `run()` Method:**
- It's executed with the current market state, printing out the trader data and observations.
- It iterates over the products, using the market depth to decide on orders and compiles them into the result dictionary.
- Trader data is updated to reflect the strategy's adaptiveness, and a conversions value is set, possibly indicating the number of conversions from one currency to another or similar metrics.

**Usage:**
This class can be instantiated and used to simulate trading strategies in a mock trading environment, where it will perform actions based on the state of the market, with the aim of maximizing profit within the defined risk parameters.
