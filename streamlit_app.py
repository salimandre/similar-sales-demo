import altair as alt
import pandas as pd
import streamlit as st
import json
#import matplotlib.pyplot as plt
#import numpy as np
#import plotly.express as px

# Utils
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
    "Accessibility": "♿"
}

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

# Show the page title and description.
st.set_page_config(page_title="Similar Products", page_icon="🏝️")
st.title("🏝️ Similar Products")
st.write(
    """
    This app visualizes results from similar products algorithm.
    It shows for each selected live sale the top similar sales based on different dimensions!
    Just click on the widgets below to explore!
    """
)

# Load the data from a CSV. We're caching this so it doesn't reload every time the app
# reruns (e.g. if the user interacts with the widgets).
@st.cache_data
def load_data():
    rankings_df = pd.read_csv("data/similar_products_rankings.csv")
    sales_display_names_df = pd.read_csv("data/similar_products_display_names.csv")
    sales_features_df = pd.read_csv("data/similar_products_features.csv")
    with open("data/similar_products_feature_cols.json", 'r') as f:
        sales_features_cols_json = json.load(f)
    return rankings_df, sales_display_names_df, sales_features_df, sales_features_cols_json


rankings_df, sales_display_names_df, sales_features_df, sales_features_cols_json = load_data()

# Thematic feature df
location_sales_features_df = sales_features_df[['sale_uid']+sales_features_cols_json['location']]
pricing_sales_features_df = sales_features_df[['sale_uid']+sales_features_cols_json['pricing']]
equipment_service_sales_features_df = sales_features_df[['sale_uid']+sales_features_cols_json['equipment_service']]
stay_type_sales_features_df = sales_features_df[['sale_uid']+sales_features_cols_json['stay_type']]
accessibility_sales_features_df = sales_features_df[['sale_uid']+sales_features_cols_json['accessibility']]


# Adding selection box by sale display name 
selected_sale = st.selectbox(
    "Select a sale:",
    sales_display_names_df['sale_display_name'],
    index=3
)

# Get the Sale ID for the selected sale
#sale_uid_to_name_dict = sales_display_names_df.drop_duplicates().set_index('sale_uid')['sale_display_name'].to_dict()
sale_name_to_uid_dict = sales_display_names_df.drop_duplicates().set_index('sale_display_name')['sale_uid'].to_dict()
selected_sale_uid = sale_name_to_uid_dict.get(selected_sale)
selected_culture = selected_sale_uid[:5]
selected_sale_id = extract_sale_id(selected_sale_uid)

# Display the Sale URL to the user
#st.write(f"You selected: {selected_sale}")
selected_sale_url = sale_url_template.format(insert_sale_id=selected_sale_id)
st.markdown(f"You selected: [{selected_sale}]({selected_sale_url}) (culture: {selected_culture}, id: {selected_sale_id})")

# Show a multiselect widget with the sale dimensions using `st.multiselect`.
selected_sale_dimensions = st.multiselect(
    "Dimensions",
    list(available_sale_dimensions.keys()),
    ["Location", "Pricing"],
)

# Show a slider widget with the years using `st.slider`.
top = st.slider("Top", 1, 10, (1, 5))
min_rank = top[0]
max_rank = top[1]

selected_rankings_df = rankings_df[rankings_df['sale_uid_a'] == selected_sale_uid]

all_top_sales_dict = {}
for dim in available_sale_dimensions:
    if dim in selected_sale_dimensions:

        # Prepare top offers
        dim_sim_col = available_sale_dimensions.get(dim) + '__similarity'
        dim_rank_col = available_sale_dimensions.get(dim) + '__similarity_rank'
        
        dim_top_sales_df = selected_rankings_df.sort_values(by=dim_rank_col, ascending=True).iloc[min_rank-1:max_rank]
        dim_top_sales_df = dim_top_sales_df[["sale_uid_a", "sale_uid_b", dim_rank_col, dim_sim_col]].rename(columns={dim_rank_col: "rank", dim_sim_col: "similarity"})
        
        dim_top_sales_df['sale_url'] = [display_url_html(sale_url_template.format(insert_sale_id=extract_sale_id(s_uid))) for s_uid in dim_top_sales_df["sale_uid_b"]]

        # Display dimension
        st.text("\n\n")
        st.markdown(f"### {available_sale_dimensions_emojis.get(dim)} Top Results for {dim}")
        #st.markdown(dim_top_sales_df[['rank', 'similarity', 'sale_url']].to_html(escape=False, index=False), unsafe_allow_html=True)

        dim_top_sales_df['dimension'] = dim
        all_top_sales_dict[dim] = dim_top_sales_df

        for i in range(max_rank - min_rank + 1):
            # Prepare offer
            offer = get_dict_from_df(all_top_sales_dict[dim].iloc[[i]])

            with st.container():
                # Display Offer Details
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                col1.markdown(f"**#{offer['rank']}**")
                col2.markdown(f"**Similarity:** {offer['similarity']:.3f}")
                col3.markdown(f"{offer['sale_url']}", unsafe_allow_html=True)

                # Add a button in col4 to toggle chart display
                if col4.button("Explain", key=f"toggle_{dim}_{offer['rank']}"):
                    # Toggle the display state in session state
                    key = f"show_chart_{offer['rank']}"
                    if key not in st.session_state:
                        st.session_state[key] = True
                    else:
                        st.session_state[key] = not st.session_state[key]

                # Condition to display the text based on the toggle state
                if st.session_state.get(f"show_chart_{offer['rank']}", False):
                    dict1 = get_dict_from_df(location_sales_features_df[location_sales_features_df['sale_uid'] == 'fr_fr412030'])
                    dict2 = get_dict_from_df(location_sales_features_df[location_sales_features_df['sale_uid'] == 'fr_fr411914'])
                    common_features, different_features = compare_features(dict1, dict2)

                    # Format feature names
                    relevant_keys = set(common_features+different_features)
                    feats_1 = {k.split('__')[1]: dict1[k] for k in relevant_keys}
                    feats_2 = {k.split('__')[1]: dict2[k] for k in relevant_keys}

                    # Remove prefix for the DataFrame display
                    filtered_dict1 = {k: v for k, v in feats_1.items()}
                    filtered_dict2 = {k: v for k, v in feats_2.items()}

                    #df = pd.DataFrame([filtered_dict1, filtered_dict2], index=['Dict1', 'Dict2']).T
                    
                    # Prepare DataFrame for Altair
                    df = pd.DataFrame({
                        'Feature': list(filtered_dict1.keys()) + list(filtered_dict2.keys()),
                        'Value': list(filtered_dict1.values()) + list(filtered_dict2.values()),
                        'Source': ['Dict1'] * len(filtered_dict1) + ['Dict2'] * len(filtered_dict2)
                    })

                    # Create horizontal bar chart with Altair
                    chart = alt.Chart(df).mark_bar().encode(
                        x=alt.X('Value:Q', axis=alt.Axis(title='Value')),
                        y=alt.Y('Feature:N', axis=alt.Axis(title='Feature'), sort='-x'),
                        color='Source:N',
                        tooltip=['Feature:N', 'Value:Q', 'Source:N']
                    ).properties(
                        title="Comparison of Features",
                        width=600,
                        height=400
                    )

                    st.altair_chart(chart)

                    st.altair_chart(chart)

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

# Add explainability

# Button to toggle the display of the sentence
if st.button('Explain'):
    # Use session state to track toggle state
    st.session_state.show_hello = not st.session_state.get('show_hello', False)

# Condition to display the text based on the toggle state
if st.session_state.get('show_hello', False):
    dict1 = get_dict_from_df(location_sales_features_df[location_sales_features_df['sale_uid'] == 'fr_fr412030'])
    dict2 = get_dict_from_df(location_sales_features_df[location_sales_features_df['sale_uid'] == 'fr_fr411914'])
    common_features, different_features = compare_features(dict1, dict2)

    # Format feature names
    relevant_keys = set(common_features+different_features)
    feats_1 = {k.split('__')[1]: dict1[k] for k in relevant_keys}
    feats_2 = {k.split('__')[1]: dict2[k] for k in relevant_keys}

    # Remove prefix for the DataFrame display
    filtered_dict1 = {k: v for k, v in feats_1.items()}
    filtered_dict2 = {k: v for k, v in feats_2.items()}

    #df = pd.DataFrame([filtered_dict1, filtered_dict2], index=['Dict1', 'Dict2']).T
    
    # Prepare DataFrame for Altair
    df = pd.DataFrame({
        'Feature': list(filtered_dict1.keys()) + list(filtered_dict2.keys()),
        'Value': list(filtered_dict1.values()) + list(filtered_dict2.values()),
        'Source': ['Dict1'] * len(filtered_dict1) + ['Dict2'] * len(filtered_dict2)
    })

    # Create horizontal bar chart with Altair
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Value:Q', axis=alt.Axis(title='Value')),
        y=alt.Y('Feature:N', axis=alt.Axis(title='Feature'), sort='-x'),
        color='Source:N',
        tooltip=['Feature:N', 'Value:Q', 'Source:N']
    ).properties(
        title="Comparison of Features",
        width=600,
        height=400
    )

    st.altair_chart(chart)

# Footer
st.markdown("---")  # Horizontal line for separation
st.markdown(
    """
    <div style='text-align: center;'>
        Made with 💖 by <strong>Gautier</strong>, <strong>Jean-Luc</strong> and <strong>Corentin</strong>
    </div>
    """,
    unsafe_allow_html=True
)