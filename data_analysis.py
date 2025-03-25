import pandas as pd

def identify_outliers(df, column):
    """
    Function to identify outliers in a given numeric column using the IQR method.
    Returns a DataFrame containing the outlier rows.
    """
    # Convert data to numeric, coercing errors to NaN
    numeric_data = pd.to_numeric(df[column].str.strip(), errors='coerce')

    # Calculate Q1 (25th percentile) and Q3 (75th percentile), ignoring NaN values
    Q1 = numeric_data.quantile(0.25)
    Q3 = numeric_data.quantile(0.75)
    IQR = Q3 - Q1

    # Define bounds for outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Identify outliers based on the index alignment
    outliers = df[(numeric_data < lower_bound) | (numeric_data > upper_bound)].copy()

    return outliers

def filter_short_surveys(df, start_column, end_column):
    """
    Filters surveys that took less than 20 minutes.

    Parameters:
    df (DataFrame): The DataFrame containing survey data.
    start_column (str): The name of the column with start times.
    end_column (str): The name of the column with end times.

    Returns:
    DataFrame: A filtered DataFrame.
    """

    # Ensure columns exist
    if start_column not in df.columns or end_column not in df.columns:
        raise ValueError(f"Columns '{start_column}' or '{end_column}' not found in DataFrame.")

    # Convert to datetime with proper timezone handling
    df[start_column] = pd.to_datetime(df[start_column], errors='coerce', utc=True)
    df[end_column] = pd.to_datetime(df[end_column], errors='coerce', utc=True)

    # Check if conversion was successful
    if df[start_column].isna().all():
        raise ValueError(f"Column '{start_column}' could not be converted to datetime. Check data for invalid formats.")
    if df[end_column].isna().all():
        raise ValueError(f"Column '{end_column}' could not be converted to datetime. Check data for invalid formats.")

    # Convert to local timezone (remove UTC awareness)
    df[start_column] = df[start_column].dt.tz_convert(None)
    df[end_column] = df[end_column].dt.tz_convert(None)

    # Calculate duration in minutes (use absolute value to correct negative durations)
    df['duration'] = abs((df[end_column] - df[start_column]).dt.total_seconds() / 60.0)

    # Filter surveys that took less than 20 minutes
    short_surveys = df[df['duration'] < 20]

    # Remove columns that contain only null values
    filtered_df = short_surveys.dropna(axis=1, how='all')

    return filtered_df

def check_data_consistency(df, rules):
    error_counts = {}

    for rule in rules:
        q1, a1 = rule['question_1'], rule['expected_answer_1']
        q2, invalid_value = rule['question_2'], rule['invalid_answer_2_contains']
        label = rule['error_label']

        inconsistent_rows = df[
            (df[q1] == a1) &
            (df[q2].str.lower().str.contains(invalid_value.lower(), na=False))
        ]

        error_counts[label] = len(inconsistent_rows)

    return error_counts
