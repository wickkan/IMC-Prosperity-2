import pandas as pd
import numpy as np
import importlib.util
import matplotlib.pyplot as plt
import importlib.util
from sklearn.linear_model import LinearRegression

# Replace 'file_paths' with the paths to your CSV files
file_paths = ['/Users/kanishkaw/Desktop/Tech/IMC-Prosperity2/Round1/Round1_DataAnalysis/prices_round_1_day_-2.csv',
              '/Users/kanishkaw/Desktop/Tech/IMC-Prosperity2/Round1/Round1_DataAnalysis/prices_round_1_day_-1.csv', '/Users/kanishkaw/Desktop/Tech/IMC-Prosperity2/Round1/Round1_DataAnalysis/prices_round_1_day_0.csv']
starfruit_dataframes = []

for file_path in file_paths:
    df = pd.read_csv(file_path, delimiter=';')
    df_starfruit = df[df['product'] == 'STARFRUIT']
    starfruit_dataframes.append(df_starfruit)

# Combine all dataframes into one
combined_starfruit_df = pd.concat(starfruit_dataframes)

# Calculate daily average price and volatility
daily_starfruit_stats = combined_starfruit_df.groupby('day').agg({
    'mid_price': ['mean', 'std', 'count']
}).reset_index()

daily_starfruit_stats.columns = [
    'Day', 'Average Price', 'Volatility', 'Transaction Count']

# Check for a trend using a simple linear regression
model = LinearRegression()
model.fit(daily_starfruit_stats['Day'].values.reshape(-1, 1),
          daily_starfruit_stats['Average Price'].values)

trend_line = model.predict(daily_starfruit_stats['Day'].values.reshape(-1, 1))

# Plot the results
plt.figure(figsize=(12, 6))
plt.plot(daily_starfruit_stats['Day'],
         daily_starfruit_stats['Average Price'], label='Average Price')
plt.plot(daily_starfruit_stats['Day'],
         trend_line, label='Trend Line', color='red')
plt.title('STARFRUIT Daily Average Price and Trend')
plt.xlabel('Day')
plt.ylabel('Average Price')
plt.legend()
plt.show()

# Calculate rolling statistics for visual trend and volatility assessment
rolling_window = 5  # Example of a 5-day rolling window
combined_starfruit_df['rolling_mean'] = combined_starfruit_df['mid_price'].rolling(
    window=rolling_window).mean()
combined_starfruit_df['rolling_std'] = combined_starfruit_df['mid_price'].rolling(
    window=rolling_window).std()

# Plot rolling statistics
plt.figure(figsize=(12, 6))
plt.plot(combined_starfruit_df['mid_price'], color='blue', label='Original')
plt.plot(combined_starfruit_df['rolling_mean'],
         color='red', label='Rolling Mean')
plt.plot(combined_starfruit_df['rolling_std'],
         color='black', label='Rolling Std Dev')
plt.legend(loc='best')
plt.title('STARFRUIT Price with Rolling Mean & Standard Deviation')
plt.show()

# Check if the price fluctuations are consistent across the period
plt.figure(figsize=(12, 6))
plt.plot(daily_starfruit_stats['Day'],
         daily_starfruit_stats['Volatility'], label='Volatility', color='orange')
plt.title('STARFRUIT Price Volatility Over Time')
plt.xlabel('Day')
plt.ylabel('Volatility (Standard Deviation)')
plt.legend()
plt.show()
