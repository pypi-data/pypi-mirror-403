"""Module modulo2 in sub2 package."""

import pandas as pd

# Sample data for the DataFrame
data = {
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "City": ["New York", "Los Angeles", "Chicago"],
}


# Function to get the DataFrame
def get_dataframe() -> pd.DataFrame:
    """Returns a DataFrame constructed from the sample data."""
    return pd.DataFrame(data)


# Function to get the average age
def get_average_age(dataframe: pd.DataFrame) -> float:
    """Returns the average age from the DataFrame."""
    return dataframe["Age"].mean()
