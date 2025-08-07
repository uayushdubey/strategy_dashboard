import streamlit as st
import pandas as pd

# Load the dataset
file_path = r"output_trade_signals.xlsx"
df = pd.read_excel(file_path)

# Convert DATETIME to datetime format
df['DATETIME'] = pd.to_datetime(df['DATETIME'])
df = df.sort_values(by=['STOCK_NAME', 'DATETIME'])

# Lot sizes mapping
lot_sizes = {
    'ADANIENT': 300, 'ADANIPORTS': 475, 'ASIANPAINT': 250, 'AXISBANK': 625,
    'BAJAJ-AUTO': 75, 'BAJAJFINSV': 500, 'BAJFINANCE': 750, 'BHARTIARTL': 475,
    'BPCL': 1975, 'BRITANNIA': 125, 'CIPLA': 375, 'COALINDIA': 1350,
    'DIVISLAB': 100, 'DRREDDY': 625, 'EICHERMOT': 175, 'GRASIM': 250,
    'HCLTECH': 350, 'HDFCBANK': 550, 'HDFCLIFE': 1100, 'HEROMOTOCO': 150,
    'HINDALCO': 1400, 'HINDUNILVR': 300, 'ICICIBANK': 700, 'INDUSINDBK': 700,
    'INFY': 400, 'ITC': 1600, 'JSWSTEEL': 675, 'KOTAKBANK': 400, 'LT': 175,
    'M&M': 200, 'MARUTI': 50, 'NESTLEIND': 250, 'NTPC': 1500, 'ONGC': 2250,
    'POWERGRID': 1900, 'RELIANCE': 500, 'SBILIFE': 375, 'SBIN': 750,
    'SHREECEM': 25, 'SUNPHARMA': 350, 'TATACONSUM': 550, 'TATAMOTORS': 800,
    'TATASTEEL': 5500, 'TCS': 175, 'TECHM': 600, 'TITAN': 175,
    'ULTRACEMCO': 50, 'UPL': 1355, 'WIPRO': 3000
}

# Prepare processed signals
processed = []

for stock in df['STOCK_NAME'].unique():
    stock_df = df[df['STOCK_NAME'] == stock].reset_index(drop=True)
    i = 0
    while i < len(stock_df):
        row = stock_df.iloc[i]
        if row['BUY_SELL_Signal'] in ['BUY', 'SELL']:
            entry_date = row['DATETIME']
            signal = row['BUY_SELL_Signal']
            entry_price = round(row['CLOSE'], 2)

            for j in range(i + 1, len(stock_df)):
                exit_row = stock_df.iloc[j]
                if (
                    (signal == 'BUY' and exit_row['EXIT_Signal'] == 'EXIT_LONG') or
                    (signal == 'SELL' and exit_row['EXIT_Signal'] == 'EXIT_SHORT')
                ):
                    exit_date = exit_row['DATETIME']
                    exit_price = round(exit_row['CLOSE'], 2)
                    pnl = int(exit_row['P&L'])
                    lot_size = lot_sizes.get(stock, 1)
                    pnl_per_lot = pnl * lot_size

                    processed.append({
                        'STOCK_NAME': stock,
                        'ENTRY_DATETIME': entry_date,
                        'ENTRY_PRICE': entry_price,
                        'EXIT_DATETIME': exit_date,
                        'EXIT_PRICE': exit_price,
                        'SIGNAL': signal,
                        'P&L': pnl,
                        'P&L per Lot': pnl_per_lot
                    })
                    i = j
                    break
        i += 1

signals_df = pd.DataFrame(processed)

# Add month and year for filters
signals_df['Month'] = signals_df['ENTRY_DATETIME'].dt.strftime('%B')
signals_df['Year'] = signals_df['ENTRY_DATETIME'].dt.year

# Streamlit UI
st.set_page_config(page_title="Trade Signal Dashboard", layout="wide")
st.title("📊 Trade Signal Dashboard")

# Dropdowns in columns on top-left
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    stock_list = ['All Stocks'] + sorted(signals_df['STOCK_NAME'].unique())
    selected_stock = st.selectbox("Select Stock", stock_list)
with col2:
    year_list = ['All Years'] + sorted(signals_df['Year'].unique())
    selected_year = st.selectbox("Select Year", year_list)
with col3:
    month_list = ['All Months'] + list(pd.date_range(start='2020-01-01', periods=12, freq='MS').strftime('%B'))
    selected_month = st.selectbox("Select Month", month_list)

# Apply filters
filtered_df = signals_df.copy()
if selected_stock != 'All Stocks':
    filtered_df = filtered_df[filtered_df['STOCK_NAME'] == selected_stock]
if selected_year != 'All Years':
    filtered_df = filtered_df[filtered_df['Year'] == selected_year]
if selected_month != 'All Months':
    filtered_df = filtered_df[filtered_df['Month'] == selected_month]

# Format entry and exit prices as strings with 2 decimals for display
filtered_df['ENTRY_PRICE'] = filtered_df['ENTRY_PRICE'].apply(lambda x: f"{x:.2f}")
filtered_df['EXIT_PRICE'] = filtered_df['EXIT_PRICE'].apply(lambda x: f"{x:.2f}")

# Color function for P&L columns
def color_pnl(val):
    try:
        val = float(val)
        return f'color: {"green" if val > 0 else "red" if val < 0 else "black"}'
    except:
        return ''

# Show dataframe with styled P&L and P&L per Lot
st.dataframe(
    filtered_df.drop(columns=['Month', 'Year']).style.applymap(color_pnl, subset=['P&L', 'P&L per Lot']),
    use_container_width=True
)

# Summary stats
total_trades = len(filtered_df)
total_pnl_per_lot = filtered_df['P&L per Lot'].sum()
avg_pnl_per_trade = round(total_pnl_per_lot / total_trades, 2) if total_trades > 0 else 0

st.markdown(
    f"""
    <div style='display: flex; gap: 50px; flex-wrap: wrap;'>
        <h4 style='color:green;'>📦 Total P&L per Lot: {total_pnl_per_lot}</h4>
        <h4 style='color:black;'>📊 Total Trades: {total_trades}</h4>
        <h4 style='color:black;'>📈 Average P&L per Trade: {avg_pnl_per_trade}</h4>
    </div>
    """,
    unsafe_allow_html=True
)

