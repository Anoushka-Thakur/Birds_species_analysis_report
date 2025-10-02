import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

# --- Configuration ---
st.set_page_config(
    page_title="Birds Observation Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define file paths based on likely separate data files
FOREST_FILE = "bird_observations_forest.csv"
GRASSLAND_FILE = "bird_observations_grassland.csv"

# --- 1. Data Loading and Preprocessing ---

@st.cache_data
def load_and_preprocess_data(forest_path, grassland_path):
    """Loads and preprocesses data from two ecosystems."""
    try:
        # Load data, ensuring to handle potential Excel file if path is wrong
        forest_df = pd.read_csv(forest_path)
        grassland_df = pd.read_csv(grassland_path)

        # Standardize column names (Crucial for later merging/comparison)
        # Note: You may need to adjust the column names here if they are different in your original files
        forest_df.columns = [col + '_forest' for col in forest_df.columns]
        grassland_df.columns = [col + '_grassland' for col in grassland_df.columns]

        # Convert date columns
        date_cols_f = [col for col in forest_df.columns if 'Date' in col]
        for col in date_cols_f:
            forest_df[col] = pd.to_datetime(forest_df[col], errors='coerce')
            
        date_cols_g = [col for col in grassland_df.columns if 'Date' in col]
        for col in date_cols_g:
            grassland_df[col] = pd.to_datetime(grassland_df[col], errors='coerce')

        # Combine: Assuming we want a union of observations, not a row-by-row merge.
        # We find the smallest dataframe size to ensure safe concatenation for visual comparison
        max_rows = min(len(forest_df), len(grassland_df))
        merged_df = pd.concat([forest_df.head(max_rows), grassland_df.head(max_rows)], axis=1)
        
        return merged_df, forest_df, grassland_df
    
    except FileNotFoundError:
        st.error(f"Data files not found. Please ensure '{FOREST_FILE}' and '{GRASSLAND_FILE}' are in the project folder.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred during data loading or preprocessing: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

MERGED_DF, FOREST_DF, GRASSLAND_DF = load_and_preprocess_data(FOREST_FILE, GRASSLAND_FILE)

if MERGED_DF.empty:
    st.stop()
    
# --- 2. Shared Functions ---

def render_habitat_analysis(df, habitat_name, suffix):
    """Renders charts and data analysis for a single habitat (Forest or Grassland)."""
    
    # Define required columns based on suffix (e.g., '_forest')
    common_name_col = f'Common_Name{suffix}'
    id_method_col = f'ID_Method{suffix}'
    flyover_col = f'Flyover_Observed{suffix}'
    plot_name_col = f'Plot_Name{suffix}'

    # Basic column check
    if not all(col in df.columns for col in [common_name_col, id_method_col, flyover_col, plot_name_col]):
        st.warning(f"Required columns not found in {habitat_name} data. Cannot render charts.")
        return

    # --- Analysis 1: Top 10 Species ---
    st.subheader(f"Top 10 Most Observed Species")
    top_species = df[common_name_col].value_counts().nlargest(10).reset_index(name='Count')
    top_species.columns = ['Common_Name', 'Count']
    
    fig_top_species = px.bar(
        top_species,
        x='Common_Name',
        y='Count',
        title=f'Top 10 Species in {habitat_name}',
        color='Count',
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={'Common_Name': 'Species Name', 'Count': 'Observation Count'}
    )
    st.plotly_chart(fig_top_species, use_container_width=True)
    
    # --- Analysis 2: ID Method Distribution (Pie Chart) ---
    st.subheader(f"Observation Method Distribution")
    # Correct aggregation: name the count column explicitly
    id_method_species = df.groupby(id_method_col)[common_name_col].nunique().reset_index(name='Unique_Species_Count')
    
    fig_id_method_pie = px.pie(
        id_method_species,
        values='Unique_Species_Count',
        names=id_method_col,
        title=f'Proportion of Unique Species by ID Method ({habitat_name})'
    )
    st.plotly_chart(fig_id_method_pie, use_container_width=True)

    # --- Analysis 3: Flyover Counts (Bar Chart) ---
    st.subheader(f"Flyover vs. Resident Observations")
    
    # Correct aggregation: Exclude 'Unknown' and name columns explicitly
    flyover_counts = df[df[flyover_col].astype(str).str.lower() != 'unknown'][flyover_col].value_counts().reset_index()
    flyover_counts.columns = ['Flyover_Status', 'Observation_Count']
    
    fig_flyover = px.bar(
        flyover_counts, 
        x='Flyover_Status', 
        y='Observation_Count', 
        title=f'Flyover Observation Counts ({habitat_name})',
        color='Observation_Count',
        labels={'Flyover_Status': 'Flyover Observation Status', 'Observation_Count': 'Number of Observations'}
    )
    st.plotly_chart(fig_flyover, use_container_width=True)

    # --- Analysis 4: Plot-level Diversity ---
    st.subheader(f"Plot Diversity ({habitat_name})")
    
    # Correct aggregation: Calculate unique species per plot
    plot_species_count = df.groupby(plot_name_col)[common_name_col].nunique().reset_index(name='Unique_Species_Count')
    
    # Sort the data (which was causing a KeyError before)
    plot_species_count_sorted = plot_species_count.sort_values(by='Unique_Species_Count', ascending=False)
    
    fig_plot_diversity = px.bar(
        plot_species_count_sorted.head(10),
        x=plot_name_col,
        y='Unique_Species_Count',
        title=f'Top 10 Plots by Unique Species Count ({habitat_name})',
        color='Unique_Species_Count',
        color_continuous_scale=px.colors.sequential.Agsunset,
        labels={plot_name_col: 'Observation Plot', 'Unique_Species_Count': 'Unique Species Found'}
    )
    st.plotly_chart(fig_plot_diversity, use_container_width=True)


# --- 3. Streamlit Dashboard Layout ---

st.title("🦅 Birds Observation Habitat Comparison")
st.markdown("""
This dashboard analyzes bird species distribution, diversity, and observation methods 
across two distinct habitats: **Forest** and **Grassland**.
""")
st.markdown("---")

# Display key metrics at the top
st.subheader("Ecosystem Summary Metrics")
col1, col2 = st.columns(2)

try:
    if 'Common_Name_forest' in FOREST_DF.columns and 'Common_Name_grassland' in GRASSLAND_DF.columns:
        unique_species_forest = FOREST_DF['Common_Name_forest'].nunique()
        unique_species_grassland = GRASSLAND_DF['Common_Name_grassland'].nunique()
        total_obs_forest = len(FOREST_DF)
        total_obs_grassland = len(GRASSLAND_DF)
        
        col1.metric("Unique Species (Forest)", unique_species_forest, delta=f"{total_obs_forest} Total Observations")
        col2.metric("Unique Species (Grassland)", unique_species_grassland, delta=f"{total_obs_grassland} Total Observations")
    else:
        st.info("Cannot calculate summary metrics. Check if data contains 'Common_Name' column.")
except Exception as e:
    st.error(f"Error calculating metrics: {e}")


# Tabbed visualization for habitat comparison
tab_forest, tab_grassland = st.tabs(["🌳 Forest Habitat", "🌾 Grassland Habitat"])

with tab_forest:
    render_habitat_analysis(FOREST_DF, 'Forest', '_forest')

with tab_grassland:
    render_habitat_analysis(GRASSLAND_DF, 'Grassland', '_grassland')
