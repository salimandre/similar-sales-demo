import altair as alt
import pandas as pd
import streamlit as st

# Show the page title and description.
st.set_page_config(page_title="Similar Products", page_icon="🏝️")
st.title("🏝️ Similar Products")
st.write(
    """
    This app visualizes data from [The Movie Database (TMDB)](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata).
    It shows which movie genre performed best at the box office over the years. Just 
    click on the widgets below to explore!
    This is a new line
    """
)


# Load the data from a CSV. We're caching this so it doesn't reload every time the app
# reruns (e.g. if the user interacts with the widgets).
@st.cache_data
def load_data():
    df = pd.read_csv("data/movies_genres_summary.csv")
    sales_display_names_df = pd.read_csv("data/similar_products_display_names.csv")
    return df, sales_display_names_df


df, sales_display_names_df = load_data()

# Show a multiselect widget with the sales using `st.multiselect`.
#sale_names = st.multiselect(
#    "Sales",
#    sales_display_names_df.sale_display_name.unique(),
#    #["Action", "Adventure", "Biography", "Comedy", "Drama", "Horror"],
#)

selected_sale = st.selectbox(
    "Select a sale:",
    sales_display_names_df['sale_display_name'],
    index=3
)

# Get the Sale ID for the selected sale
selected_sale_uid = sales_display_names_df[sales_display_names_df['sale_display_name'] == selected_sale]['sale_uid'].iloc[0]
selected_culture = selected_sale_uid[:5]
selected_sale_id = int(''.join(filter(str.isdigit, selected_sale_uid)))

# Display the Sale URL to the user
#st.write(f"You selected: {selected_sale}")
sale_url = f"https://www.voyage-prive.com/fiche-produit/details/{selected_sale_id}/b1"
st.markdown(f"You selected: [{selected_sale}]({sale_url})")

# Show a multiselect widget with the genres using `st.multiselect`.
sale_dimensions = st.multiselect(
    "Dimensions",
    ["Location", "Pricing", "Stay Type", "Equipment & Services", "Accessibility"],
    ["Location", "Pricing", "Stay Type", "Equipment & Services", "Accessibility"],
)

# Show a slider widget with the years using `st.slider`.
top = st.slider("Top", 1, 10, (1, 5))


