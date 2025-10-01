# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

st.title('Bird Species Observation Analysis')



def load_data(file_path_1, file_path_2):
    
    combined_data_1 = None
    combined_data_2 = None

    try:
        # Forest data
        excel_data_1 = pd.ExcelFile(file_path_1)
        sheet_names_1 = excel_data_1.sheet_names
        sheet_dict_1 = {}
        for sheet_name in sheet_names_1:
            sheet_dict_1[sheet_name] = excel_data_1.parse(sheet_name)
        combined_data_1 = pd.concat(sheet_dict_1.values(), ignore_index=True)

        # Grassland data
        excel_data_2 = pd.ExcelFile(file_path_2)
        sheet_names_2 = excel_data_2.sheet_names
        sheet_dict_2 = {}
        for sheet_name in sheet_names_2:
            sheet_dict_2[sheet_name] = excel_data_2.parse(sheet_name)
        combined_data_2 = pd.concat(sheet_dict_2.values(), ignore_index=True)

    except FileNotFoundError as e:
        st.error(f"Error loading file: {e}")
    except Exception as e:
        st.error(f"An error occurred during data loading: {e}")

    return combined_data_1, combined_data_2



def preprocess_data(df_forest, df_grassland):
    
    if df_forest is None or df_grassland is None:
        return None

    with st.spinner('Merging data...'):
        merged_df = pd.merge(df_forest, df_grassland, on='AcceptedTSN', how='outer', suffixes=('_forest', '_grassland'))

    with st.spinner('Filling missing values...'):
        # Fill numerical columns with 0
        numerical_cols = merged_df.select_dtypes(include=['number']).columns
        merged_df[numerical_cols] = merged_df[numerical_cols].fillna(0)

        # Fill object/categorical columns with 'Unknown'
        object_cols = merged_df.select_dtypes(include=['object']).columns
        merged_df[object_cols] = merged_df[object_cols].fillna('Unknown')

    with st.spinner('Converting data types...'):
        # change datatypes
        merged_df['Date_forest'] = pd.to_datetime(merged_df['Date_forest'], format='%Y-%m-%d', errors='coerce')
        merged_df['Date_grassland'] = pd.to_datetime(merged_df['Date_grassland'], format='%Y-%m-%d', errors='coerce')
        merged_df['Start_Time_forest'] = pd.to_datetime(merged_df['Start_Time_forest'], format='%H:%M:%S', errors='coerce').dt.time
        merged_df['End_Time_forest'] = pd.to_datetime(merged_df['End_Time_forest'], format='%H:%M:%S', errors='coerce').dt.time
        merged_df['Start_Time_grassland'] = pd.to_datetime(merged_df['Start_Time_grassland'], format='%H:%M:%S', errors='coerce').dt.time
        merged_df['End_Time_grassland'] = pd.to_datetime(merged_df['End_Time_grassland'], format='%H:%M:%S', errors='coerce').dt.time

    return merged_df



# File paths (replace with actual paths)
file_path_forest = 'C:\\Users\\anous\\OneDrive\\PROJECTS\\BIRD SPECIES OBSERVATION PROJECT\\Bird_Monitoring_Data_FOREST.XLSX'
file_path_grassland = 'C:\\Users\\anous\\OneDrive\\PROJECTS\\BIRD SPECIES OBSERVATION PROJECT\\Bird_Monitoring_Data_GRASSLAND.XLSX'

# Load data with spinner
with st.spinner('Loading data...'):
    forest_df, grassland_df = load_data(file_path_forest, file_path_grassland)

# Preprocess data with spinner
if forest_df is not None and grassland_df is not None:
    processed_df = preprocess_data(forest_df, grassland_df)
    if processed_df is not None:
        st.success('Data loading and preprocessing complete!')
        st.write("Processed Data:")
        st.write(processed_df.head()) # Display first few rows of processed data
else:
    processed_df = None
    st.error("Data loading failed. Please check file paths.")
if processed_df is not None:
    st.header("Temporal Analysis")

    # Extract temporal features
    processed_df['Year'] = processed_df['Date_forest'].dt.year
    processed_df['Month'] = processed_df['Date_forest'].dt.month
    processed_df['Season'] = processed_df['Month'].map({
        1: 'Winter', 2: 'Winter', 3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer', 9: 'Autumn', 10: 'Autumn',
        11: 'Autumn', 12: 'Winter'
    })

    # Analyze Observation Time
    st.subheader("Observation Time Analysis")
    filtered_df = processed_df.dropna(subset=['Start_Time_forest', 'Start_Time_grassland'], how='all')
    filtered_df = filtered_df[
        (filtered_df['Start_Time_forest'] != 'Unknown') |
        (filtered_df['Start_Time_grassland'] != 'Unknown')
    ]

    # Convert time objects to strings before extracting hours to handle potential mixed types
    filtered_df['Start_Hour_forest'] = pd.to_datetime(filtered_df['Start_Time_forest'].astype(str), format='%H:%M:%S', errors='coerce').dt.hour
    filtered_df['Start_Hour_grassland'] = pd.to_datetime(filtered_df['Start_Time_grassland'].astype(str), format='%H:%M:%S', errors='coerce').dt.hour

    all_start_hours = pd.concat([filtered_df['Start_Hour_forest'], filtered_df['Start_Hour_grassland']]).dropna()
    start_hour_counts = all_start_hours.value_counts().sort_index()

    st.write("Distribution of start hours:")
    st.write(start_hour_counts)

    fig_start_hour_line = px.line(start_hour_counts, x=start_hour_counts.index, y='count', title='Distribution of Bird Observation Start Hours (Line Chart)')
    fig_start_hour_line.update_layout(xaxis_title='Hour', yaxis_title='Count')
    st.plotly_chart(fig_start_hour_line)

    # Analyze seasonal trends
    st.subheader("Seasonal Trends")
    seasonal_species_count = processed_df[processed_df['Season'] != 'Unknown'].groupby('Season')['AcceptedTSN'].nunique().reset_index()
    seasonal_species_count.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)

    st.write("Unique species count by Season:")
    st.write(seasonal_species_count)

    fig_seasonal_trends = px.bar(seasonal_species_count, x='Season', y='Unique_Species_Count', title='Unique Species Count by Season')
    fig_seasonal_trends.update_layout(xaxis_title='Season', yaxis_title='Unique Species Count')
    st.plotly_chart(fig_seasonal_trends)
if processed_df is not None:
    st.header("Spatial Analysis")

    # Location Insight
    st.subheader("Location Insight")
    location_species_count = processed_df[processed_df['Location_Type_forest'] != 'Unknown'].groupby('Location_Type_forest')['AcceptedTSN'].nunique().reset_index()
    location_species_count.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("Unique species count by Location Type (Forest):")
    st.write(location_species_count)

    location_species_count_grassland = processed_df[processed_df['Location_Type_grassland'] != 'Unknown'].groupby('Location_Type_grassland')['AcceptedTSN'].nunique().reset_index()
    location_species_count_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("Unique species count by Location Type (Grassland):")
    st.write(location_species_count_grassland)

    # Plot Level Analysis
    st.subheader("Plot Level Analysis Top 10 Plots")
    plot_species_count_forest = processed_df[processed_df['Plot_Name_forest'] != 'Unknown'].groupby('Plot_Name_forest')['AcceptedTSN'].nunique().reset_index()
    plot_species_count_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    plot_species_count_forest_sorted = plot_species_count_forest.sort_values(by='Unique_Species_Count', ascending=False).head(10)
    st.write("Unique species count by Plot Name (Forest) - Sorted Descending:")
    st.write(plot_species_count_forest_sorted)

    plot_species_count_grassland = processed_df[processed_df['Plot_Name_grassland'] != 'Unknown'].groupby('Plot_Name_grassland')['AcceptedTSN'].nunique().reset_index()
    plot_species_count_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    plot_species_count_grassland_sorted = plot_species_count_grassland.sort_values(by='Unique_Species_Count', ascending=False).head(10)
    st.write("Unique species count by Plot Name (Grassland) - Sorted Descending:")
    st.write(plot_species_count_grassland_sorted)

    # Create and display sorted bar charts for unique species count by plot name (forest)
    fig_plot_forest_sorted = px.bar(plot_species_count_forest_sorted, x='Plot_Name_forest', y='Unique_Species_Count', title='Unique Species Count by Plot Name (Forest) - Sorted')
    fig_plot_forest_sorted.update_layout(xaxis_title='Forest', yaxis_title='Unique Species Count')
    st.plotly_chart(fig_plot_forest_sorted)

    # Create and display sorted bar charts for unique species count by plot name (grassland)
    fig_plot_grassland_sorted = px.bar(plot_species_count_grassland_sorted, x='Plot_Name_grassland', y='Unique_Species_Count', title='Unique Species Count by Plot Name (Grassland) - Sorted')
    fig_plot_grassland_sorted.update_layout(xaxis_title='Grassland', yaxis_title='Unique Species Count')
    st.plotly_chart(fig_plot_grassland_sorted)
if processed_df is not None:
    st.header("Observer Trends")

    # Analyze Observer Bias
    st.subheader("Observer Bias")
    observer_species_count_forest = processed_df[processed_df['Observer_forest'] != 'Unknown'].groupby('Observer_forest')['AcceptedTSN'].nunique().reset_index()
    observer_species_count_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("Unique species count by Observer (Forest):")
    st.write(observer_species_count_forest)

    observer_species_count_grassland = processed_df[processed_df['Observer_grassland'] != 'Unknown'].groupby('Observer_grassland')['AcceptedTSN'].nunique().reset_index()
    observer_species_count_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("Unique species count by Observer (Grassland):")
    st.write(observer_species_count_grassland)

    # Create and display pie charts for observer trends
    fig_observer_forest_pie = px.pie(observer_species_count_forest, values='Unique_Species_Count', names='Observer_forest', title='Proportion of Unique Species by Observer (Forest)',
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_observer_forest_pie)

    fig_observer_grassland_pie = px.pie(observer_species_count_grassland, values='Unique_Species_Count', names='Observer_grassland', title='Proportion of Unique Species by Observer (Grassland)',
                                      color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_observer_grassland_pie)

    # Analyze Visit Patterns
    st.subheader("Visit Analysis")
    visit_species_count_forest = processed_df[processed_df['Visit_forest'] != 'Unknown'].groupby('Visit_forest')['AcceptedTSN'].nunique().reset_index()
    visit_species_count_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("Unique species count by Visit (Forest):")
    st.write(visit_species_count_forest)

    visit_species_count_grassland = processed_df[processed_df['Visit_grassland'] != 'Unknown'].groupby('Visit_grassland')['AcceptedTSN'].nunique().reset_index()
    visit_species_count_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("Unique species count by Visit (Grassland):")
    st.write(visit_species_count_grassland)
if processed_df is not None:
    st.header("Environmental Analysis")
    st.subheader("Weather Correlation")

    # Analyze average number of unique species by temperature (forest)
    avg_species_temp_forest = processed_df[processed_df['Temperature_forest'] != 0].groupby('Temperature_forest')['AcceptedTSN'].nunique().reset_index()
    avg_species_temp_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count', 'Temperature_forest': 'Temperature_forest (°C)'}, inplace=True)
    st.write("Unique species count by Temperature (Forest):")
    st.write(avg_species_temp_forest.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze average number of unique species by humidity (forest)
    avg_species_humidity_forest = processed_df[processed_df['Humidity_forest'] != 0].groupby('Humidity_forest')['AcceptedTSN'].nunique().reset_index()
    avg_species_humidity_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by Humidity (Forest):")
    st.write(avg_species_humidity_forest.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze average number of unique species by sky condition (forest)
    avg_species_sky_forest = processed_df[processed_df['Sky_forest'] != 'Unknown'].groupby('Sky_forest')['AcceptedTSN'].nunique().reset_index()
    avg_species_sky_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by Sky Condition (Forest):")
    st.write(avg_species_sky_forest.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze average number of unique species by wind condition (forest)
    avg_species_wind_forest = processed_df[processed_df['Wind_forest'] != 'Unknown'].groupby('Wind_forest')['AcceptedTSN'].nunique().reset_index()
    avg_species_wind_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by Wind Condition (Forest):")
    st.write(avg_species_wind_forest.sort_values(by='Unique_Species_Count', ascending=False))

    # Create scatter plots for weather correlation (forest)
    fig_temp_forest_scatter = px.scatter(avg_species_temp_forest, x='Temperature_forest (°C)', y='Unique_Species_Count', title='Unique Species Count by Temperature (Forest)')
    st.plotly_chart(fig_temp_forest_scatter)

    fig_humidity_forest_scatter = px.scatter(avg_species_humidity_forest, x='Humidity_forest', y='Unique_Species_Count', title='Unique Species Count by Humidity (Forest)')
    st.plotly_chart(fig_humidity_forest_scatter)

    fig_sky_forest_scatter = px.scatter(avg_species_sky_forest, x='Sky_forest', y='Unique_Species_Count', title='Unique Species Count by Sky Condition (Forest)')
    st.plotly_chart(fig_sky_forest_scatter)

    fig_wind_forest_scatter = px.scatter(avg_species_wind_forest, x='Wind_forest', y='Unique_Species_Count', title='Unique Species Count by Wind Condition (Forest)')
    st.plotly_chart(fig_wind_forest_scatter)


    # Analyze average number of unique species by temperature (grassland)
    avg_species_temp_grassland = processed_df[processed_df['Temperature_grassland'] != 0].groupby('Temperature_grassland')['AcceptedTSN'].nunique().reset_index()
    avg_species_temp_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count', 'Temperature_grassland': 'Temperature_grassland (°C)'}, inplace=True)
    st.write("\nUnique species count by Temperature (Grassland):")
    st.write(avg_species_temp_grassland.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze average number of unique species by humidity (grassland)
    avg_species_humidity_grassland = processed_df[processed_df['Humidity_grassland'] != 0].groupby('Humidity_grassland')['AcceptedTSN'].nunique().reset_index()
    avg_species_humidity_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by Humidity (Grassland):")
    st.write(avg_species_humidity_grassland.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze average number of unique species by sky condition (grassland)
    avg_species_sky_grassland = processed_df[processed_df['Sky_grassland'] != 'Unknown'].groupby('Sky_grassland')['AcceptedTSN'].nunique().reset_index()
    avg_species_sky_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by Sky Condition (Grassland):")
    st.write(avg_species_sky_grassland.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze average number of unique species by wind condition (grassland)
    avg_species_wind_grassland = processed_df[processed_df['Wind_grassland'] != 'Unknown'].groupby('Wind_grassland')['AcceptedTSN'].nunique().reset_index()
    avg_species_wind_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by Wind Condition (Grassland):")
    st.write(avg_species_wind_grassland.sort_values(by='Unique_Species_Count', ascending=False))

    # Create scatter plots for weather correlation (grassland)
    fig_temp_grassland_scatter = px.scatter(avg_species_temp_grassland, x='Temperature_grassland (°C)', y='Unique_Species_Count', title='Unique Species Count by Temperature (Grassland)')
    st.plotly_chart(fig_temp_grassland_scatter)

    fig_humidity_grassland_scatter = px.scatter(avg_species_humidity_grassland, x='Humidity_grassland', y='Unique_Species_Count', title='Unique Species Count by Humidity (Grassland)')
    st.plotly_chart(fig_humidity_grassland_scatter)

    fig_sky_grassland_scatter = px.scatter(avg_species_sky_grassland, x='Sky_grassland', y='Unique_Species_Count', title='Unique Species Count by Sky Condition (Grassland)')
    st.plotly_chart(fig_sky_grassland_scatter)

    fig_wind_grassland_scatter = px.scatter(avg_species_wind_grassland, x='Wind_grassland', y='Unique_Species_Count', title='Unique Species Count by Wind Condition (Grassland)')
    st.plotly_chart(fig_wind_grassland_scatter)

    st.subheader("Disturbance Effect")

    # Analyze Disturbance Effect
    disturbance_species_count_forest = processed_df[processed_df['Disturbance_forest'] != 'Unknown'].groupby('Disturbance_forest')['AcceptedTSN'].nunique().reset_index()
    disturbance_species_count_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("Unique species count by Disturbance (Forest):")
    st.write(disturbance_species_count_forest.sort_values(by='Unique_Species_Count', ascending=False))

    disturbance_species_count_grassland = processed_df[processed_df['Disturbance_grassland'] != 'Unknown'].groupby('Disturbance_grassland')['AcceptedTSN'].nunique().reset_index()
    disturbance_species_count_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by Disturbance (Grassland):")
    st.write(disturbance_species_count_grassland.sort_values(by='Unique_Species_Count', ascending=False))
if processed_df is not None:
    st.header("Conservation Insights")
    st.subheader("Watchlist trends")

    # Calculate and display unique species count by PIF_Watchlist_Status_forest
    watchlist_counts_forest = processed_df[processed_df['PIF_Watchlist_Status_forest'] != 'Unknown'].groupby('PIF_Watchlist_Status_forest')['AcceptedTSN'].nunique().reset_index()
    watchlist_counts_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("Unique species count by PIF Watchlist Status (Forest):")
    st.write(watchlist_counts_forest)

    # Calculate and display unique species count by PIF_Watchlist_Status_grassland
    watchlist_counts_grassland = processed_df[processed_df['PIF_Watchlist_Status_grassland'] != 'Unknown'].groupby('PIF_Watchlist_Status_grassland')['AcceptedTSN'].nunique().reset_index()
    watchlist_counts_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by PIF Watchlist Status (Grassland):")
    st.write(watchlist_counts_grassland)

    # Create and display Plotly bar chart for PIF Watchlist Status (forest)
    fig_watchlist_forest = px.bar(watchlist_counts_forest, x='PIF_Watchlist_Status_forest', y='Unique_Species_Count', title='Unique Species Count by PIF Watchlist Status (Forest)')
    st.plotly_chart(fig_watchlist_forest)

    # Create and display Plotly bar chart for PIF Watchlist Status (grassland)
    fig_watchlist_grassland = px.bar(watchlist_counts_grassland, x='PIF_Watchlist_Status_grassland', y='Unique_Species_Count', title='Unique Species Count by PIF Watchlist Status (Grassland)')
    st.plotly_chart(fig_watchlist_grassland)

    # Calculate and display unique species count by Regional_Stewardship_Status_forest
    stewardship_counts_forest = processed_df[processed_df['Regional_Stewardship_Status_forest'] != 'Unknown'].groupby('Regional_Stewardship_Status_forest')['AcceptedTSN'].nunique().reset_index()
    stewardship_counts_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by Regional Stewardship Status (Forest):")
    st.write(stewardship_counts_forest)

    # Calculate and display unique species count by Regional_Stewardship_Status_grassland
    stewardship_counts_grassland = processed_df[processed_df['Regional_Stewardship_Status_grassland'] != 'Unknown'].groupby('Regional_Stewardship_Status_grassland')['AcceptedTSN'].nunique().reset_index()
    stewardship_counts_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by Regional Stewardship Status (Grassland):")
    st.write(stewardship_counts_grassland)

    # Create and display Plotly bar chart for Regional Stewardship Status (forest)
    fig_stewardship_forest = px.bar(stewardship_counts_forest, x='Regional_Stewardship_Status_forest', y='Unique_Species_Count', title='Unique Species Count by Regional Stewardship Status (Forest)')
    st.plotly_chart(fig_stewardship_forest)

    # Create and display Plotly bar chart for Regional Stewardship Status (grassland)
    fig_stewardship_grassland = px.bar(stewardship_counts_grassland, x='Regional_Stewardship_Status_grassland', y='Unique_Species_Count', title='Unique Species Count by Regional Stewardship Status (Grassland)')
    st.plotly_chart(fig_stewardship_grassland)

    st.subheader("AOU patterns")

    # Calculate and display unique species count by AOU_Code_forest
    aou_code_counts_forest = processed_df[processed_df['AOU_Code_forest'] != 'Unknown'].groupby('AOU_Code_forest')['AcceptedTSN'].nunique().reset_index()
    aou_code_counts_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    # Merge with scientific names and common names
    aou_code_counts_forest = pd.merge(aou_code_counts_forest, processed_df[['AOU_Code_forest', 'Scientific_Name_forest', 'Common_Name_forest']].drop_duplicates(), on='AOU_Code_forest', how='left')
    st.write("Unique species count by AOU Code (Forest):")
    st.write(aou_code_counts_forest.sort_values(by='Unique_Species_Count', ascending=False))

    # Calculate and display unique species count by AOU_Code_grassland
    aou_code_counts_grassland = processed_df[processed_df['AOU_Code_grassland'] != 'Unknown'].groupby('AOU_Code_grassland')['AcceptedTSN'].nunique().reset_index()
    aou_code_counts_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    # Merge with scientific names and common names
    aou_code_counts_grassland = pd.merge(aou_code_counts_grassland, processed_df[['AOU_Code_grassland', 'Scientific_Name_grassland', 'Common_Name_grassland']].drop_duplicates(), on='AOU_Code_grassland', how='left')
    st.write("\nUnique species count by AOU Code (Grassland):")
    st.write(aou_code_counts_grassland.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze and display AOU codes related to PIF Watchlist status (Forest)
    pif_watchlist_aou_forest = processed_df[(processed_df['PIF_Watchlist_Status_forest'] == True) & (processed_df['AOU_Code_forest'] != 'Unknown')].groupby(['AOU_Code_forest', 'Scientific_Name_forest', 'Common_Name_forest'])['AcceptedTSN'].nunique().reset_index()
    pif_watchlist_aou_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nAOU Codes on PIF Watchlist (Forest):")
    st.write(pif_watchlist_aou_forest.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze and display AOU codes related to Regional Stewardship status (Forest)
    stewardship_aou_forest = processed_df[(processed_df['Regional_Stewardship_Status_forest'] == True) & (processed_df['AOU_Code_forest'] != 'Unknown')].groupby(['AOU_Code_forest', 'Scientific_Name_forest', 'Common_Name_forest'])['AcceptedTSN'].nunique().reset_index()
    stewardship_aou_forest.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nAOU Codes with Regional Stewardship Status (Forest):")
    st.write(stewardship_aou_forest.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze and display AOU codes related to PIF Watchlist status (Grassland)
    pif_watchlist_aou_grassland = processed_df[(processed_df['PIF_Watchlist_Status_grassland'] == True) & (processed_df['AOU_Code_grassland'] != 'Unknown')].groupby(['AOU_Code_grassland', 'Scientific_Name_grassland', 'Common_Name_grassland'])['AcceptedTSN'].nunique().reset_index()
    pif_watchlist_aou_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nAOU Codes on PIF Watchlist (Grassland):")
    st.write(pif_watchlist_aou_grassland.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze and display AOU codes related to Regional Stewardship status (Grassland)
    stewardship_aou_grassland = processed_df[(processed_df['Regional_Stewardship_Status_grassland'] == True) & (processed_df['AOU_Code_grassland'] != 'Unknown')].groupby(['AOU_Code_grassland', 'Scientific_Name_grassland', 'Common_Name_grassland'])['AcceptedTSN'].nunique().reset_index()
    stewardship_aou_grassland.rename(columns={'AcceptedTSN': 'Unique_Species_Count'}, inplace=True)
    st.write("\nAOU Codes with Regional Stewardship Status (Grassland):")
    st.write(stewardship_aou_grassland.sort_values(by='Unique_Species_Count', ascending=False))
if processed_df is not None:
    st.header("Distance and Behaviour")
    st.subheader("Flyover frequency")

# 1. Calculate and display flyover observation counts (Forest)
flyover_counts_forest = processed_df[processed_df['Flyover_Observed_forest'] != 'Unknown']['Flyover_Observed_forest'].value_counts().reset_index()

# 2. Assign clear, distinct names to the two columns:
# The first column is the category/status, the second is the calculated count
flyover_counts_forest.columns = ['Flyover_Status', 'Observation_Count']
print("Flyover observation counts (Forest):")
print(flyover_counts_forest) 

fig_flyover_forest = px.bar(
    flyover_counts_forest, 
    x='Flyover_Status', # Use the new status column name
    y='Observation_Count', # Use the new count column name
    title='Flyover Observation Counts (Forest)',
    color='Observation_Count',
    labels={'Flyover_Status': 'Flyover Observation Status', 'Observation_Count': 'Number of Observations'}

)
st.plotly_chart(fig_flyover_forest) # For Streamlit
fig_flyover_forest.show()



# 1. Calculate the counts for Flyover_Observed_grassland, excluding 'Unknown'
flyover_counts_grassland = processed_df[processed_df['Flyover_Observed_grassland'] != 'Unknown']['Flyover_Observed_grassland'].value_counts().reset_index()

# 2. Assign clear, distinct names to the two columns:
# The first column is the category/status, the second is the calculated count
flyover_counts_grassland.columns = ['Flyover_Status', 'Observation_Count']

print("Flyover observation counts (Grassland):")
print(flyover_counts_grassland)

# Create the bar chart using Plotly Express
# Use the new column names for clarity

fig_flyover_grassland = px.bar(
    flyover_counts_grassland, 
    x='Flyover_Status', # Use the new status column name
    y='Observation_Count', # Use the new count column name
    title='Flyover Observation Counts (Grassland)',
    color='Observation_Count',
    labels={'Flyover_Status': 'Flyover Observation Status', 'Observation_Count': 'Number of Observations'}

)
#st.plotly_chart(fig_flyover_grassland, use_container_width=True) # For Streamlit
st.plotly_chart(fig_flyover_grassland)
fig_flyover_grassland.show()

if processed_df is not None:
    st.header("ID Method")
    st.subheader("ID method used by common name")

    # Analyze ID Method by Common Name (Forest)
    id_method_species_forest = processed_df[processed_df['ID_Method_forest'] != 'Unknown'].groupby('ID_Method_forest')['Common_Name_forest'].nunique().reset_index()
    id_method_species_forest.rename(columns={'Common_Name_forest': 'Unique_Species_Count'}, inplace=True)
    st.write("Unique species count by ID Method (Forest):")
    st.write(id_method_species_forest.sort_values(by='Unique_Species_Count', ascending=False))

    # Analyze ID Method by Common Name (Grassland)
    id_method_species_grassland = processed_df[processed_df['ID_Method_grassland'] != 'Unknown'].groupby('ID_Method_grassland')['Common_Name_grassland'].nunique().reset_index()
    id_method_species_grassland.rename(columns={'Common_Name_grassland': 'Unique_Species_Count'}, inplace=True)
    st.write("\nUnique species count by ID Method (Grassland):")
    st.write(id_method_species_grassland.sort_values(by='Unique_Species_Count', ascending=False))

    # Create a pie chart for ID Method (forest)
    fig_id_method_forest_pie = px.pie(id_method_species_forest, values='Unique_Species_Count', names='ID_Method_forest', title='Proportion of Unique Species by ID Method (Forest)')
    st.plotly_chart(fig_id_method_forest_pie)

    # Create a pie chart for ID Method (grassland)
    fig_id_method_grassland_pie = px.pie(id_method_species_grassland, values='Unique_Species_Count', names='ID_Method_grassland', title='Proportion of Unique Species by ID Method (Grassland)')
    st.plotly_chart(fig_id_method_grassland_pie)

    # Analyze Common Name by ID Method (Forest - showing top methods for each species)
    common_name_methods_forest = processed_df[processed_df['ID_Method_forest'] != 'Unknown'].groupby(['Common_Name_forest', 'ID_Method_forest']).size().reset_index(name='Count')
    common_name_methods_forest = common_name_methods_forest.sort_values(by=['Common_Name_forest', 'Count'], ascending=[True, False])
    st.write("\nTop ID Methods for each Common Name (Forest):")
    st.write(common_name_methods_forest.head())

    # Analyze Common Name by ID Method (Grassland - showing top methods for each species)
    common_name_methods_grassland = processed_df[processed_df['ID_Method_grassland'] != 'Unknown'].groupby(['Common_Name_grassland', 'ID_Method_grassland']).size().reset_index(name='Count')
    common_name_methods_grassland = common_name_methods_grassland.sort_values(by=['Common_Name_grassland', 'Count'], ascending=[True, False])
    st.write("\nTop ID Methods for each Common Name (Grassland):")
    st.write(common_name_methods_grassland.head())

  ## KEY INSIGHTS
  
  
  ##### Based on the analysis we've performed, here are some conclusions and suggestions regarding the bird monitoring data in forest and grassland locations:

### 1. Temporal Analysis:
##### The majority of bird observations occurred during the Spring and Summer seasons, which aligns with typical bird activity patterns during breeding and migration periods.

##### Observation times are concentrated in the early morning hours, peaking around 7:00 AM. This suggests that monitoring efforts are effectively targeting the most active periods for birds.

### 2. Spatial Analysis:

##### Both forest and grassland locations show a similar number of unique species observed.
##### Plot-level analysis revealed variations in unique species counts across different plots within both forest and grassland areas. Some plots consistently show higher species diversity than others.

## 3. Observer Trends:

##### There are differences in the number of unique species observed by different observers. Elizabeth Oswald recorded the highest number of unique species in both forest and grassland locations. This could indicate differences in observer experience, effort, or the specific areas surveyed by each observer.

## 4. Environmental Analysis (Weather Correlation):

##### The analysis of unique species count by temperature, humidity, sky condition, and wind condition provides insights into the preferred environmental conditions for bird sightings. For example, certain temperature and humidity ranges appear to be associated with higher unique species counts. Clear or partly cloudy skies and light air movement also seem to correlate with more unique species observations.

## 5. Conservation Insights:

##### The PIF Watchlist Status and Regional Stewardship Status analysis highlight species that are of conservation concern. We identified specific AOU codes corresponding to species on the PIF Watchlist and those with Regional Stewardship status in both forest and grassland locations. This information is crucial for prioritizing conservation efforts.

## 6. Distance and Behavior (Flyover Frequency):

##### The flyover frequency analysis shows that a significant number of birds are observed flying over the areas, particularly in grasslands. This suggests that monitoring methods are capturing both birds within the plot and those passing through.

## 7. ID Method:

##### The ID method analysis indicates that 'Singing' and 'Visualization' are the most common methods used for identifying unique species in both locations. This information can be useful for evaluating the effectiveness of different survey techniques.


