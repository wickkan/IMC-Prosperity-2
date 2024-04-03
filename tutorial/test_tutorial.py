from datamodel import TradingState, Listing, OrderDepth, Trade
from tutorial import Trader  # Adjust the import path based on your project structure


def generate_mock_trading_state():
    timestamp = 123456
    listings = {
        "AMETHYSTS": Listing("AMETHYSTS", "AMETHYSTS", "SEASHELLS"),
        "STARFRUIT": Listing("STARFRUIT", "STARFRUIT", "SEASHELLS"),
    }
    order_depths = {
        "AMETHYSTS": OrderDepth(),
        "STARFRUIT": OrderDepth(),
    }

    # Manually set the buy_orders and sell_orders after instantiation
    order_depths["AMETHYSTS"].buy_orders = {10: 7, 9: 5}
    order_depths["AMETHYSTS"].sell_orders = {11: -4, 12: -8}
    order_depths["STARFRUIT"].buy_orders = {142: 3, 141: 5}
    order_depths["STARFRUIT"].sell_orders = {144: -5, 145: -8}

    position = {"AMETHYSTS": 10, "STARFRUIT": 10}
    state = TradingState(
        traderData="", timestamp=timestamp, listings=listings,
        order_depths=order_depths, own_trades={}, market_trades={},
        position=position, observations={}
    )
    return state


if __name__ == "__main__":
    # Generate mock trading state
    mock_state = generate_mock_trading_state()

    # Initialize and test your Trader
    trader = Trader()
    result, conversions, traderData = trader.run(mock_state)

    # Print or log the results for analysis
    print("Trading Results:", result)
    print("Conversions:", conversions)
    print("Trader Data:", traderData)
    # Add more detailed logging or analysis as needed
