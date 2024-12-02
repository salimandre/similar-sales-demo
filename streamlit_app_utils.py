import altair as alt
import pandas as pd
import streamlit as st
import json


# Constants and configuration
PAGE_CONFIG = {"page_title": "Similar Products", "page_icon": "🏝️"}
DEFAULT_SELECTIONS = {"Dimensions": ["Location", "Equipment & Services"], "Top": (1, 5)}
DATA_FILES = {
    "rankings": "data/similar_products_rankings.csv",
    "display_names": "data/similar_products_display_names.csv",
    "features": "data/similar_products_features.csv",
    "feature_cols": "data/similar_products_feature_cols.json"
}

# Utils
def get_utils():
    sale_url_template = "https://www.voyage-prive.com/fiche-produit/details/{insert_sale_id}/b1"
    extract_sale_id = lambda sale_id_str: int(''.join(filter(str.isdigit, sale_id_str)))
    display_url_html = lambda url: f'<a href="{url}" target="_blank">View Sale</a>'
    get_dict_from_df = lambda df: df.to_dict(orient='records')[0]

    available_sale_dimensions =  \
        {
            "Location": "location",
            "Pricing": "pricing", 
            "Stay Type": "stay_type",
            "Equipment & Services": "equipment_service",
            "Accessibility": "accessibility"
        }

    available_sale_dimensions_emojis = {
        "Location": "📍",
        "Pricing": "💰",
        "Stay Type": "🕶️",
        "Equipment & Services": "⛳",
        "Accessibility": "♿",
        "Global": "🌐"
    }

    return sale_url_template, extract_sale_id, display_url_html, \
                get_dict_from_df, available_sale_dimensions, \
                    available_sale_dimensions_emojis

def load_json_file(filepath):
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Failed to load JSON file: {filepath}")
        st.exception(e)
        return {}

def load_csv(filepath):
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        st.error(f"Failed to load CSV file: {filepath}")
        st.exception(e)
        return pd.DataFrame()

# returns the list of common features between 2 sales
# and the the list of distinct features
def compare_features(dict1, dict2):
    common = []
    diff = []
    # Iterate through all unique keys that might appear in either dictionary
    all_keys = set(dict1).union(dict2)
    for key in all_keys:
        val1 = dict1.get(key, 0)  # Default to 0 if key is not found
        val2 = dict2.get(key, 0)  # Default to 0 if key is not found
        if val1 == val2 == 1:
            common.append(key)
        elif val1 != val2 and (val1 == 1 or val2 == 1):
            diff.append(key)
    return common, diff

# Load the data from a CSV. We're caching this so it doesn't reload every time the app
# reruns (e.g. if the user interacts with the widgets).
@st.cache_data
def load_data():
    rankings_df = load_csv(DATA_FILES["rankings"])
    sales_display_names_df = load_csv(DATA_FILES["display_names"])
    sales_features_df = load_csv(DATA_FILES["features"])
    sales_features_cols_json = load_json_file(DATA_FILES["feature_cols"])

    # Thematic feature dfs
    thematic_features = \
    {
        "Location": sales_features_df[['sale_uid']+sales_features_cols_json['location']],
        "Pricing": sales_features_df[['sale_uid']+sales_features_cols_json['pricing']],
        "Equipment & Services": sales_features_df[['sale_uid']+sales_features_cols_json['equipment_service']],
        "Stay Type": sales_features_df[['sale_uid']+sales_features_cols_json['stay_type']],
        "Accessibility": sales_features_df[['sale_uid']+sales_features_cols_json['accessibility']]
    }

    return rankings_df, sales_display_names_df, sales_features_df, sales_features_cols_json, thematic_features

# Get the Sale ID for the selected sale
def get_selected_sale_details(sales_display_names_df, selected_sale_name):
    _, extract_sale_id, _, _, _, _ = get_utils()

    sale_uid_to_name_dict = sales_display_names_df.drop_duplicates().set_index('sale_uid')['sale_display_name'].to_dict()
    sale_name_to_uid_dict = sales_display_names_df.drop_duplicates().set_index('sale_display_name')['sale_uid'].to_dict()
    selected_sale_uid = sale_name_to_uid_dict.get(selected_sale_name)
    selected_culture = selected_sale_uid[:5]
    selected_sale_id = extract_sale_id(selected_sale_uid)

    return selected_culture, selected_sale_uid, selected_sale_id, sale_name_to_uid_dict, sale_uid_to_name_dict

def display_chart_rank_v_similarity(all_top_sales_dict):
    """
    Creates and displays an Altair chart visualizing rankings and similarities across different dimensions.
    Args:
        all_top_sales_dict (dict): A dictionary where keys are dimensions and values are DataFrames with ranking data.
    """
    # combine rankings for similarity plot
    combined_dim_top_sales_df = pd.concat(
        all_top_sales_dict.values(),
        ignore_index=True
    )

    chart = alt.Chart(combined_dim_top_sales_df).mark_circle(size=100).encode(
        x=alt.X('rank:Q', title='Rank'),
        y=alt.Y('similarity:Q', title='Similarity', scale=alt.Scale(domain=[0, 1])),
        color=alt.Color(
            'dimension:N',
            title='Dimension',
            scale=alt.Scale(scheme='category10')
        ),
        tooltip=['rank', 'similarity', 'dimension']  # Add tooltips for interactivity
    ).properties(
        width=800,
        height=400,
        title="Rank vs. Similarity by Dimension"
    )

    st.altair_chart(chart, use_container_width=True)
