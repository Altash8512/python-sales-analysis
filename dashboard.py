import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    """Loads the sales data, performs cleaning, and returns a DataFrame."""
    try:
        df = pd.read_csv('sales_data.csv')
    except FileNotFoundError:
        st.error("The 'sales_data.csv' file was not found. Please make sure it is in the same directory as the script.")
        return None
    
    # --- Standardize Column Names ---
    # Strip whitespace from headers and convert to a consistent case to prevent KeyErrors
    df.columns = df.columns.str.strip().str.replace(' ', '_')

    # Drop the 'Unnamed:_0' column if it exists
    if 'Unnamed:_0' in df.columns:
        df.drop('Unnamed:_0', axis=1, inplace=True)

    # Rename columns to be more descriptive and consistent
    rename_dict = {
        'Order_Date': 'Date',
        'Quantity_Ordered': 'Units_Sold',
        'Price_Each': 'Unit_Price',
        'Sales': 'Revenue'
    }
    df.rename(columns=rename_dict, inplace=True)
    
    # --- Data Cleaning ---
    # Convert 'Date' to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # --- Feature Engineering (to match notebook logic) ---
    # Create 'Cost' and 'Profit' columns. Assuming a 70% cost for demonstration.
    df['Cost'] = df['Revenue'] * 0.70
    df['Profit'] = df['Revenue'] - df['Cost']

    # --- Correctly extract City for Region mapping ---
    df['City_Name'] = df['Purchase_Address'].apply(lambda x: x.split(',')[1].strip())

    # Create 'Region' from 'City'
    def get_region(city):
        if city in ['New York City', 'Boston']:
            return 'East'
        elif city in ['San Francisco', 'Los Angeles']:
            return 'West'
        elif city in ['Dallas', 'Atlanta']:
            return 'South'
        elif city in ['Seattle', 'Portland']:
            return 'North'
        else:
            return 'Central' # Austin and any other fallbacks
    df['Region'] = df['City_Name'].apply(get_region)

    # Create 'Category' from 'Product'
    def get_category(product):
        if any(p in product for p in ['Laptop', 'Monitor', 'PC']):
            return 'Electronics'
        elif any(p in product for p in ['iPhone', 'Phone']):
            return 'Mobile'
        elif any(p in product for p in ['Cable', 'Headphones', 'Wired', 'Charger', 'Machine']):
            return 'Accessories'
        else:
            return 'Other'
    df['Category'] = df['Product'].apply(get_category)
            
    # Remove duplicates
    df.drop_duplicates(inplace=True)
    
    return df

def main():
    st.set_page_config(page_title="Sales Dashboard", layout="wide")
    st.title("Sales Data Analysis Dashboard")

    df = load_data()
    if df is None:
        # Stop execution if data loading failed
        return

    # --- Sidebar Filters ---
    st.sidebar.header("Filters")
    selected_region = st.sidebar.multiselect(
        "Region",
        options=df["Region"].unique(),
        default=df["Region"].unique()
    )
    selected_category = st.sidebar.multiselect(
        "Category",
        options=df["Category"].unique(),
        default=df["Category"].unique()
    )

    # Filter data based on selection
    df_filtered = df[df["Region"].isin(selected_region) & df["Category"].isin(selected_category)].copy()

    if df_filtered.empty:
        st.warning("No data available for the selected filters.")
        return

    # --- Key Metrics ---
    total_revenue = int(df_filtered["Revenue"].sum())
    total_profit = int(df_filtered["Profit"].sum())
    total_units_sold = int(df_filtered["Units_Sold"].sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_revenue:,}")
    col2.metric("Total Profit", f"${total_profit:,}")
    col3.metric("Total Units Sold", f"{total_units_sold:,}")

    st.markdown("---")

    # --- Visualizations ---
    # Monthly Revenue and Profit Trends
    st.subheader("Monthly Revenue & Profit Trends")
    df_filtered['Month'] = df_filtered['Date'].dt.to_period('M').dt.to_timestamp()
    monthly_sales = df_filtered.groupby('Month').agg({'Revenue': 'sum', 'Profit': 'sum'}).reset_index()
    fig_monthly = px.line(monthly_sales, x='Month', y=['Revenue', 'Profit'], title="Monthly Trends")
    st.plotly_chart(fig_monthly, use_container_width=True)

    # Category and Region Analysis
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Revenue by Category")
        category_revenue = df_filtered.groupby('Category')['Revenue'].sum().sort_values(ascending=False)
        fig_cat = px.bar(category_revenue, x=category_revenue.index, y='Revenue', title="Revenue by Category")
        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        st.subheader("Revenue Share by Region")
        region_revenue = df_filtered.groupby('Region')['Revenue'].sum()
        fig_region = px.pie(region_revenue, values='Revenue', names=region_revenue.index, title="Revenue Share by Region", hole=0.3)
        st.plotly_chart(fig_region, use_container_width=True)

    # Top 5 Products
    st.subheader("Top 5 Products by Revenue")
    top_5_products = df_filtered.groupby('Product')['Revenue'].sum().nlargest(5)
    fig_top_prod = px.bar(top_5_products, x=top_5_products.index, y='Revenue', title="Top 5 Products")
    st.plotly_chart(fig_top_prod, use_container_width=True)

    # Correlation Heatmap
    st.subheader("Correlation Analysis")
    numerical_cols = ['Units_Sold', 'Unit_Price', 'Revenue', 'Cost', 'Profit']
    corr_matrix = df_filtered[numerical_cols].corr()
    fig_heatmap = px.imshow(corr_matrix, text_auto=True, aspect="auto", color_continuous_scale='RdBu', title="Correlation Matrix of Numerical Features")
    st.plotly_chart(fig_heatmap, use_container_width=True)


if __name__ == "__main__":
    main()