from datamodel import OrderDepth, TradingState, Order, ConversionObservation
from typing import Dict


class Trader:

    # Constants
    SUNLIGHT_UNITS_PER_HOUR = 2500
    STORAGE_COST_PER_ORCHID = 0.1

    # Initialize with some default values
    def __init__(self):
        self.position_limits = {'ORCHIDS': 100}

    # Calculate the net cost or value after conversion considering the fees and tariffs
    def calculate_net_value(self, conversion_observation: ConversionObservation, quantity: int, selling: bool):
        if selling:
            # When selling ORCHIDS
            return (conversion_observation.bidPrice - conversion_observation.transportFees - conversion_observation.exportTariff) * quantity
        else:
            # When buying ORCHIDS
            return (conversion_observation.askPrice + conversion_observation.transportFees + conversion_observation.importTariff) * quantity

    # Main method called by the simulation
    def run(self, state: TradingState):
        result = {}
        conversions = 0
        traderData = state.traderData  # Hold any required state over iterations

        for product in state.order_depths:
            order_depth = state.order_depths[product]
            current_position = state.position.get(product, 0)
            conversion_observation: ConversionObservation = state.observations.conversionObservations[
                product]

            # Check if we have a short position to potentially cover with a conversion
            if current_position < 0:
                net_value_if_converted = self.calculate_net_value(
                    conversion_observation, current_position, selling=False)
                if net_value_if_converted < 0:  # If buying back the short position is profitable
                    conversions = current_position  # Convert the full short position

            # Check if we have a long position to potentially sell with a conversion
            elif current_position > 0:
                net_value_if_converted = self.calculate_net_value(
                    conversion_observation, current_position, selling=True)
                # If selling is profitable after storage costs
                if net_value_if_converted > (self.STORAGE_COST_PER_ORCHID * current_position):
                    conversions = -current_position  # Convert the full long position

            # Define orders based on the current market order depth and the conversions decision
            # (The actual order generation logic should be implemented here based on acceptable prices)
            # ...

        # Return the result dictionary, conversion decision, and traderData for the current iteration
        return result, conversions, traderData

# Your trading logic here
