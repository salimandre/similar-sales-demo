import altair as alt
import pandas as pd
import streamlit as st
#import plotly.express as px

# Utils
sale_url_template = "https://www.voyage-prive.com/fiche-produit/details/{insert_sale_id}/b1"
extract_sale_id = lambda sale_id_str: int(''.join(filter(str.isdigit, sale_id_str)))
display_url_html = lambda url: f'<a href="{url}" target="_blank">View Sale</a>'

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
    return rankings_df, sales_display_names_df


rankings_df, sales_display_names_df = load_data()

# Adding selection box by sale display name 
selected_sale = st.selectbox(
    "Select a sale:",
    sales_display_names_df['sale_display_name'],
    index=3
)

# Get the Sale ID for the selected sale
selected_sale_uid = sales_display_names_df[sales_display_names_df['sale_display_name'] == selected_sale]['sale_uid'].iloc[0]
selected_culture = selected_sale_uid[:5]
selected_sale_id = extract_sale_id(selected_sale_uid)

# Display the Sale URL to the user
#st.write(f"You selected: {selected_sale}")
selected_sale_url = sale_url_template.format(insert_sale_id=selected_sale_id)
st.markdown(f"You selected: [{selected_sale}]({selected_sale_url}) (culture: {selected_culture}, id: {selected_sale_id})")

# Show a multiselect widget with the sale dimensions using `st.multiselect`.
available_sale_dimensions =  \
    {
        "Location": "location",
        "Pricing": "pricing", 
        "Stay Type": "stay_type",
        "Equipment & Services": "equipment_service",
        "Accessibility": "accessibility"
    }

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

#st.write(selected_rankings_df) TO REMOVE
all_top_sales_df = {}
for dim in available_sale_dimensions:
    if dim in selected_sale_dimensions:
        dim_sim_col = available_sale_dimensions.get(dim) + '__similarity'
        dim_rank_col = available_sale_dimensions.get(dim) + '__similarity_rank'
        
        dim_top_sales_df = selected_rankings_df.sort_values(by=dim_rank_col, ascending=True).iloc[min_rank-1:max_rank]
        dim_top_sales_df = dim_top_sales_df[["sale_uid_a", "sale_uid_b", dim_rank_col, dim_sim_col]].rename(columns={dim_rank_col: "rank", dim_sim_col: "similarity"})
        
        dim_top_sales_df['sale_url'] = [display_url_html(sale_url_template.format(insert_sale_id=extract_sale_id(s_uid))) for s_uid in dim_top_sales_df["sale_uid_b"]]
        
        all_top_sales_df[dim] = dim_top_sales_df

        #st.dataframe(dim_top_sales_df[["sale_uid_a", "sale_uid_b", dim_rank_col, dim_sim_col, "sale_url"]])
        st.markdown(dim_top_sales_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        dim_top_sales_df['dimension'] = dim
        all_top_sales_df[dim] = dim_top_sales_df

# combine rankings for similarity graph
combined_dim_top_sales_df = pd.concat(
    [all_top_sales_df['Location'], all_top_sales_df['Pricing']],
    ignore_index=True
)
'''
fig = px.scatter(
    combined_dim_top_sales_df,
    x="rank",
    y="similarity",
    color="dimension",
    labels={"rank": "Rank", "similarity": "Similarity", "dimension": "Dimension"},
    title="Rank vs. Similarity by Dimension",
    range_y=[0, 1]
)

st.plotly_chart(fig)
'''

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