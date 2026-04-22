import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Profitability Analysis", layout="wide")

st.title("📊 Product Line Profitability & Margin Analysis")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    file_path = os.path.join("profitability-analysis", "data", "nassau_data.csv")
    
    df = pd.read_csv(file_path)

    # -----------------------------
    # DATA CLEANING
    # -----------------------------
    df = df.dropna()
    df = df[df['Sales'] > 0]

    # -----------------------------
    # DATE CONVERSION (FIXED)
    # -----------------------------
    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True, errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], dayfirst=True, errors='coerce')

    # Remove invalid dates
    df = df.dropna(subset=['Order Date', 'Ship Date'])

    # -----------------------------
    # FEATURE ENGINEERING
    # -----------------------------
    df['Gross Margin (%)'] = (df['Gross Profit'] / df['Sales']) * 100
    df['Profit per Unit'] = df['Gross Profit'] / df['Units']

    total_sales = df['Sales'].sum()
    total_profit = df['Gross Profit'].sum()

    df['Revenue Contribution'] = df['Sales'] / total_sales
    df['Profit Contribution'] = df['Gross Profit'] / total_profit

    # -----------------------------
    # RISK CLASSIFICATION
    # -----------------------------
    def risk_flag(margin):
        if margin < 5:
            return "Critical"
        elif margin < 15:
            return "Warning"
        else:
            return "Healthy"

    df['Risk Flag'] = df['Gross Margin (%)'].apply(risk_flag)

    return df


df = load_data()

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("🔍 Filters")

division = st.sidebar.multiselect(
    "Select Division",
    options=df['Division'].unique(),
    default=df['Division'].unique()
)

date_range = st.sidebar.date_input(
    "Select Date Range",
    [df['Order Date'].min(), df['Order Date'].max()]
)

margin_threshold = st.sidebar.slider(
    "Minimum Margin (%)",
    0, 100, 0
)

search_product = st.sidebar.text_input("Search Product")

# -----------------------------
# APPLY FILTERS
# -----------------------------
filtered_df = df[
    (df['Division'].isin(division)) &
    (df['Order Date'] >= pd.to_datetime(date_range[0])) &
    (df['Order Date'] <= pd.to_datetime(date_range[1])) &
    (df['Gross Margin (%)'] >= margin_threshold)
]

if search_product:
    filtered_df = filtered_df[
        filtered_df['Product Name'].str.contains(search_product, case=False)
    ]

# -----------------------------
# KPI METRICS
# -----------------------------
st.subheader("📌 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Sales", f"${filtered_df['Sales'].sum():,.0f}")
col2.metric("Total Profit", f"${filtered_df['Gross Profit'].sum():,.0f}")
col3.metric("Avg Margin", f"{filtered_df['Gross Margin (%)'].mean():.2f}%")

# -----------------------------
# PRODUCT PROFITABILITY
# -----------------------------
st.subheader("🏆 Top Products by Profit")

product_profit = (
    filtered_df.groupby('Product Name')['Gross Profit']
    .sum()
    .reset_index()
    .sort_values(by='Gross Profit', ascending=False)
    .head(10)
)

fig1 = px.bar(
    product_profit,
    x='Gross Profit',
    y='Product Name',
    orientation='h',
    title="Top 10 Products by Profit"
)

st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# DIVISION PERFORMANCE
# -----------------------------
st.subheader("📦 Division Performance")

division_df = filtered_df.groupby('Division').agg({
    'Sales': 'sum',
    'Gross Profit': 'sum'
}).reset_index()

fig2 = px.bar(
    division_df,
    x='Division',
    y=['Sales', 'Gross Profit'],
    barmode='group',
    title="Revenue vs Profit by Division"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# COST VS SALES
# -----------------------------
st.subheader("💸 Cost vs Sales (Risk Detection)")

fig3 = px.scatter(
    filtered_df,
    x='Cost',
    y='Sales',
    color='Risk Flag',
    hover_data=['Product Name'],
    title="Cost vs Sales Scatter Plot"
)

st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# PARETO ANALYSIS
# -----------------------------
st.subheader("📈 Profit Concentration (Pareto Analysis)")

pareto_df = (
    filtered_df.groupby('Product Name')['Gross Profit']
    .sum()
    .reset_index()
    .sort_values(by='Gross Profit', ascending=False)
)

pareto_df['Cumulative Profit'] = pareto_df['Gross Profit'].cumsum()
pareto_df['Cumulative %'] = (
    pareto_df['Cumulative Profit'] /
    pareto_df['Gross Profit'].sum()
) * 100

fig4 = px.line(
    pareto_df,
    x=pareto_df.index,
    y='Cumulative %',
    title="Cumulative Profit % (Pareto Curve)"
)

st.plotly_chart(fig4, use_container_width=True)

# -----------------------------
# INSIGHTS SECTION
# -----------------------------
st.subheader("📌 Key Insights")

st.write("• A small number of products contribute the majority of total profit.")
st.write("• Some high-revenue products operate at low margins and pose financial risk.")
st.write("• Certain divisions show imbalance between revenue and profitability.")
st.write("• Cost-heavy products with low sales should be reviewed for pricing or discontinuation.")

# -----------------------------
# DATA TABLE
# -----------------------------
st.subheader("📋 Detailed Data")

st.dataframe(filtered_df)
