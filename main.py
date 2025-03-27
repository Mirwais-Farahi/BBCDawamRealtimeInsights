import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_option_menu import option_menu
from streamlit_extras.metric_cards import style_metric_cards
from datetime import datetime
from data_loader import load_dataset
from gis_analysis import add_location_columns
from data_analysis import filter_short_surveys, check_data_consistency
from data_visualization import plot_data_quality_issues


st.set_page_config(page_title="Dashboard", page_icon="🌍", layout="wide")

# Load external CSS
def load_css(file_path):
    with open(file_path) as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css("style.css")

# Initialize dataset_load globally
dataset_load = None

def load_data(selected, submitted_after):
    global dataset_load
    dataset_load = load_dataset(selected, submitted_after=submitted_after)

def home():
    st.title("BBC - Darman Reach and Engagement Data Dashboard")
    st.markdown(
        """
        This application provides insights into BBC Darman collected data from field surveys.
        Use the navigation menu on the left to explore the data.

        ### Features:
        - Real-time Data Tracker
        - Data Quality Analaysis
        """
    )

def tracker():
    global dataset_load

    if dataset_load is not None and not dataset_load.empty:
        data = dataset_load.copy()
        col1, col2, col3, col4 = st.columns(4, gap='small')

        with col1:
            st.metric(label="Total Surveys", value=len(data), help="Total collected surveys")

        with col2:
            col_name = 'demographics_section/D6'
            if col_name in data.columns:
                data[col_name] = pd.to_numeric(data[col_name], errors='coerce')
                male_pct = (data[col_name] == 2).mean() * 100
                female_pct = (data[col_name] == 1).mean() * 100
                value = f"{male_pct:.1f} / {female_pct:.1f}"
            else:
                value = "0% / 0%"

            st.metric(label="Male / Female (%)", value=value, help="Percentage of Male and Female respondents")

        with col3:
            st.metric(label="Original vs Booster", value="0 / 0", help="Count of original vs booster surveys")

        with col4:
            st.metric(label="Surveys < 30 mins", value="0", help="Number of surveys completed in less than 30 mins")

        style_metric_cards(
            background_color="#FFFFFF",
            border_left_color="#686664",
            border_color="#000000",
            box_shadow="#F71938"
        )
        
        # --- Age Range Distribution ---
        age_col = 'demographics_section/D5'
        if age_col in data.columns:
            data[age_col] = pd.to_numeric(data[age_col], errors='coerce')
            age_bins = [0, 18, 30, 45, 60, 100]
            age_labels = ['<18', '18-30', '31-45', '46-60', '60+']
            data['age_group'] = pd.cut(data[age_col], bins=age_bins, labels=age_labels, right=False)

            # Frequency and Percentage
            freq_series = data['age_group'].value_counts().sort_index()
            pct_series = data['age_group'].value_counts(normalize=True).sort_index() * 100
            age_distribution_df = pd.DataFrame({
                'Frequency': freq_series,
                'Percentage (%)': pct_series.round(1)
            })

            # --- Styled Title with Background ---
            st.markdown(
                """
                <div style="background-color:#005055;border-radius:8px;margin-bottom:10px;">
                    <h3 style="color:#fff;padding-left:10px;font-size:18px;">Age Range Distribution</h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            # --- Layout: Table and Chart Side by Side ---
            col1, col2 = st.columns([1, 2], gap="large")

            with col1:
                st.dataframe(age_distribution_df.style.format({'Percentage (%)': '{:.1f}'}))

            with col2:
                # Enhanced Plot Design - Smaller Chart
                sns.set(style="whitegrid")
                fig, ax = plt.subplots(figsize=(5.5, 3.5))  # Reduced size for better height alignment

                sns.histplot(data[age_col].dropna(), bins=20, kde=True, stat="density", ax=ax,
                            color="#69b3a2", edgecolor="black", alpha=0.6)

                # Mean and Median Lines
                mean_age = data[age_col].mean()
                median_age = data[age_col].median()
                ax.axvline(mean_age, color='blue', linestyle='--', label=f'Mean: {mean_age:.1f}')
                ax.axvline(median_age, color='red', linestyle='-.', label=f'Median: {median_age:.1f}')

                # Styling
                ax.set_xlabel('Age', fontsize=10)
                ax.set_ylabel('Density', fontsize=10)
                ax.grid(True, linestyle='--', alpha=0.4)
                ax.legend(loc='upper right', fontsize=8)

                st.pyplot(fig)

        # --- Enumerator-wise Survey Tracker ---
        st.markdown(
            """
            <div style="background-color:#005055;border-radius:8px;margin-bottom:10px;">
                <h3 style="color:#fff;padding-left:10px;font-size:18px;">Total Surveys By Each Enumerator</District</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Define column names (adjust to your dataset's actual column names)
        enumerator_col = 'interviewer_name'         # Column with enumerator names
        province_col = 'demographics_section/D1'                  # Column with province
        district_col = 'demographics_section/D2'                  # Column with district
        date_col = 'today'                   # Column with survey date

        # Check if necessary columns exist
        required_cols = [enumerator_col, province_col, district_col, date_col]
        if all(col in data.columns for col in required_cols):
            # Convert date column to datetime
            data[date_col] = pd.to_datetime(data[date_col], errors='coerce')

            # Extract date part only
            data['survey_date_only'] = data[date_col].dt.date

            # Drop rows with missing enumerator or date
            valid_data = data.dropna(subset=[enumerator_col, 'survey_date_only'])

            # Unique enumerators list for selection
            enumerators = sorted(valid_data[enumerator_col].dropna().unique())
            selected_enum = st.selectbox("Select Enumerator", enumerators)

            # Filter data for selected enumerator
            enum_data = valid_data[valid_data[enumerator_col] == selected_enum]

            # Group by Province, District, and Date
            grouped = enum_data.groupby(
                [province_col, district_col, 'survey_date_only']
            ).size().reset_index(name='Survey Count')

            # Calculate total surveys by enumerator
            total_surveys = grouped['Survey Count'].sum()

            # Display table and total count
            st.markdown(f"**Total Surveys Collected by {selected_enum}: {total_surveys}**")
            grouped = grouped.rename(columns={
                province_col: 'Province',
                district_col: 'District',
                'survey_date_only': 'Survey Date'
            })
            st.dataframe(grouped)
        else:
            st.warning("One or more required columns for enumerator tracking are missing in the dataset.")

        # --- New Section: Survey Count by Province and District ---
        st.markdown(
            """
            <div style="background-color:#005055;border-radius:8px;margin-top:20px;margin-bottom:10px;">
                <h3 style="color:#fff;padding-left:10px;font-size:18px;">Total Survey in Each Province and District</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # --- Province Mapping ---
        province_mapping = {
            1: 'Badakhshan',
            2: 'Badghis',
            3: 'Daikundi',
            4: 'Faryab',
            5: 'Ghor',
            6: 'Herat',
            7: 'Nangarhar'
        }

        # Check if necessary columns exist
        if all(col in data.columns for col in [province_col, district_col]):
            # Map province codes to names in a new column
            data[province_col] = pd.to_numeric(data[province_col], errors='coerce')
            data['Province_Name'] = data[province_col].map(province_mapping)

            # Handle unmapped provinces (optional warning)
            if data['Province_Name'].isnull().any():
                st.warning("Some province codes were not mapped. Please check the province_mapping dictionary and data values.")

            # Group by mapped Province Name and District
            grouped = data.groupby(['Province_Name', district_col]).size().reset_index(name='Total Surveys')

            # Summary per Province for bar chart
            province_summary = data.groupby('Province_Name').size().reset_index(name='Total Surveys')
            province_summary.sort_values(by='Total Surveys', ascending=False, inplace=True)

            # Layout: Table and Chart Side by Side
            col1, col2 = st.columns([1.2, 1], gap="large")

            with col1:
                grouped_display = grouped.rename(columns={
                    'Province_Name': 'Province',
                    district_col: 'District'
                }).sort_values(by=['Province', 'District'])
                st.dataframe(grouped_display)

            with col2:
                # Bar Chart for Province-wise Survey Counts
                sns.set(style="whitegrid")
                fig, ax = plt.subplots(figsize=(6, 5))
                sns.barplot(data=province_summary, x='Total Surveys', y='Province_Name', ax=ax,
                            palette='Blues_d', edgecolor='black')
                ax.set_xlabel('Total Surveys', fontsize=12)
                ax.set_ylabel('Province', fontsize=12)
                ax.set_title('Total Surveys per Province', fontsize=14, fontweight='bold')
                for i, v in enumerate(province_summary['Total Surveys']):
                    ax.text(v + 0.5, i, str(v), color='black', va='center', fontsize=10)
                st.pyplot(fig)

        else:
            st.warning("Province and District columns are missing in the dataset.")

    else:
        st.warning("Dataset not loaded yet. Please check your data loading.")

def data_quality_review():
    global dataset_load
    data = dataset_load.copy()
    # st.write(data.columns.tolist())
    geo_column = 'start-geopoint'
    with st.expander("GPS LOCATION ANALYSIS"):
        if st.button("Add Location Data"):
            # Apply the function and update the DataFrame
            updated_df = add_location_columns(data, geo_column) 
            st.write("Updated DataFrame with Location Columns:")
            st.dataframe(updated_df)
        else:
            st.warning("No data available for the selected option.")

    # Surveys duration analysis
    with st.expander("SURVEYS DURATION ANALYSIS"):
        start_column = 'start'
        end_column = 'end'

        # Step 3: Call the function to filter short surveys
        short_survey_data = filter_short_surveys(data, start_column, end_column)

        # Display the filtered results
        if not short_survey_data.empty:
            st.write("Surveys completed in less than 30 minutes:")
            st.dataframe(short_survey_data)  # Display the filtered surveys
        else:
            st.write("No surveys found that took less than 30 minutes.")

def sidebar():
    with st.sidebar:
        st.image("data/logo.png", use_container_width=True)
        selected = option_menu(
            menu_title="Projects",
            options=["Home", "Data"],
            icons=["house", "book"],
            menu_icon="cast",
            default_index=0
        )
        st.session_state.selected_option = selected

        submitted_after = None
        if selected != "Home":
            st.subheader("Submission Date")
            submitted_after = st.date_input(
                "Select date from which to load data:",
                value=datetime.today(),
                min_value=datetime(2020, 1, 1),
                max_value=datetime.today()
            )
        st.session_state.submitted_after = submitted_after

    return selected, submitted_after

# Call sidebar first
selected_option, submitted_after = sidebar()

# Load data explicitly before displaying tabs
if selected_option != "Home":
    load_data(selected_option, submitted_after)

tab1, tab2 = st.tabs(["Tracker", "Data Quality Review"])

with tab1:
    if selected_option == "Home":
        home()
    else:
        tracker()

with tab2:
    if selected_option == "Home":
        st.info("Please select a specific project from the sidebar to access data quality review.")
    else:
        data_quality_review()
