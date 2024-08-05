import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv('db.env')

# Database credentials
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
database = os.getenv('DB_NAME')

# URL encode the password to handle special characters
password = password.replace("#", "%23").replace("!", "%21").replace("@", "%40").replace("^", "%5E").replace("&", "%26")

# Construct the connection string
connection_str = f"postgresql://{username}:{password}@{host}:{port}/{database}"
engine = create_engine(connection_str)

# Function to fetch data for the yield curve
def fetch_yield_curve_data(isin):
    query = f"""
        SELECT isin, maturity_date, yield_to_maturity
        FROM bonds_pricing
        WHERE isin IN (
            SELECT isin
            FROM bonds_reference
            WHERE lei = (
                SELECT lei
                FROM bonds_reference
                WHERE isin = '{isin}'
            )
        )
    """
    df = pd.read_sql_query(query, engine)
    return df

# Streamlit app
st.title("Bond Side-by-Side Comparison")

# ISIN input for Bond 1
isin1 = st.text_input("Enter ISIN for Bond 1")
# ISIN input for Bond 2
isin2 = st.text_input("Enter ISIN for Bond 2")

# Button to fetch data and plot
if st.button("Fetch and Compare Bonds"):
    # Fetch data for Bond 1
    df1 = fetch_yield_curve_data(isin1)
    # Fetch data for Bond 2
    df2 = fetch_yield_curve_data(isin2)

    # Create scatter plot for Bond 1
    fig = px.scatter(df1, x="maturity_date", y="yield_to_maturity", color="isin",
                     title=f"Yield Curve Comparison for Bond: {isin1}",
                     labels={"maturity_date": "Maturity Date", "yield_to_maturity": "Yield to Maturity"})
    
    # Add scatter plot for Bond 2
    fig.add_scatter(x=df2["maturity_date"], y=df2["yield_to_maturity"], mode="markers", name=f"Bond: {isin2}",
                    marker=dict(color='red', size=10))

    fig.update_traces(marker=dict(size=12),
                      selector=dict(mode='markers', name=f"Bond: {isin2}"))
    
    # Highlight selected points
    if 'selected_point' in st.session_state:
        selected_point = st.session_state.selected_point
        isin = selected_point['hovertext']
        fig.add_trace(go.Scatter(x=[selected_point['x']],
                                 y=[selected_point['y']],
                                 mode="markers",
                                 name=f"Selected Point: {isin}",
                                 marker=dict(color='yellow', size=12)))

    # Set layout
    fig.update_layout(
        xaxis_title="Maturity Date",
        yaxis_title="Yield to Maturity",
        legend_title="ISIN",
        legend=dict(x=0.02, y=0.98),
        hovermode='closest'
    )

    # Show plot
    st.plotly_chart(fig)

# Store selected point in session state
if 'clicked_point' in st.session_state:
    st.session_state.selected_point = st.session_state.clicked_point
