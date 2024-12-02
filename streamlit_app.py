import altair as alt
import pandas as pd
import streamlit as st
import json

from streamlit_app_utils import PAGE_CONFIG, DEFAULT_SELECTIONS, DATA_FILES, \
    get_utils, load_json_file, load_csv, \
    compare_features, load_data, get_selected_sale_details, display_chart_rank_v_similarity



def main():
    # Utils
    sale_url_template, extract_sale_id, display_url_html, \
    get_dict_from_df, available_sale_dimensions, \
    available_sale_dimensions_emojis = get_utils()

    # Show the page title and description.
    st.set_page_config(**PAGE_CONFIG)
    st.title(PAGE_CONFIG["page_icon"] + " Similar Products")
    st.text(
        """
        This app visualizes results from similar products algorithm.
        It shows for each selected live sale the top similar sales based on different dimensions!
        Just click on the widgets below to explore!
        """
    )

    # Load Data
    rankings_df, sales_display_names_df, sales_features_df, sales_features_cols_json, thematic_features = load_data()

    # Adding selection box by sale display name 
    selected_sale = st.selectbox(
        "Select a sale:",
        sales_display_names_df['sale_display_name'],
        index=3
    )

    # Get the Sale ID for the selected sale
    selected_culture, selected_sale_uid, selected_sale_id, sale_name_to_uid_dict, sale_uid_to_name_dict = get_selected_sale_details(sales_display_names_df, selected_sale)

    # Display the Sale URL to the user
    #st.write(f"You selected: {selected_sale}")
    selected_sale_url = sale_url_template.format(insert_sale_id=selected_sale_id)
    st.markdown(f"You selected: [{selected_sale}]({selected_sale_url}) (culture: {selected_culture}, id: {selected_sale_id})")

    # Show a multiselect widget with the sale dimensions using `st.multiselect`.
    selected_sale_dimensions = st.multiselect(
        "Dimensions",
        list(available_sale_dimensions.keys()),
        DEFAULT_SELECTIONS.get("Dimensions"),
    )

    # Show a slider widget with the years using `st.slider`.
    top = st.slider("Top", 1, 20, DEFAULT_SELECTIONS.get("Top"))
    min_rank = top[0]
    max_rank = top[1]

    selected_rankings_df = rankings_df[rankings_df['sale_uid_a'] == selected_sale_uid]

    st.header("🌟 Ranking", help='''Thematic section: sale ranking by dimension | Global section: sale ranking using all dimensions.''')
    global_ranking_section, thematic_ranking_section = st.tabs(["GLOBAL", "THEMATIC"])

    with global_ranking_section:
        dim_sim_col = 'similarity'
        dim_rank_col = 'similarity_rank'
        
        dim_top_sales_df = selected_rankings_df.sort_values(by=dim_rank_col, ascending=True).iloc[min_rank-1:max_rank]
        dim_top_sales_df = dim_top_sales_df[["sale_uid_a", "sale_uid_b", dim_rank_col, dim_sim_col]].rename(columns={dim_rank_col: "rank", dim_sim_col: "similarity"})
        
        dim_top_sales_df['sale_url'] = [display_url_html(sale_url_template.format(insert_sale_id=extract_sale_id(s_uid))) for s_uid in dim_top_sales_df["sale_uid_b"]]
        
        # Display dimension
        st.text("\n\n")
        st.markdown(f"### {available_sale_dimensions_emojis.get('Global')} Top Results")
        
        for i in range(max_rank - min_rank + 1):

            # Prepare offer
            offer = get_dict_from_df(dim_top_sales_df.iloc[[i]])

            with st.container():
                # Display Offer Details
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                col1.markdown(f"**#{offer['rank']}**")
                col2.markdown(f"**Similarity:** {offer['similarity']:.3f}")
                col3.markdown(f"{offer['sale_url']}", unsafe_allow_html=True)

        # display chart rank v similarity
        dim_top_sales_df['dimension'] = 'global'
        display_chart_rank_v_similarity(dim_top_sales_df)


    with thematic_ranking_section:
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
                        if col4.button("Explain", key=f"toggle_{dim}_{i}"):
                            # Toggle the display state in session state
                            key = f"show_chart_{dim}_{i}"
                            if key not in st.session_state:
                                st.session_state[key] = True
                            else:
                                st.session_state[key] = not st.session_state[key]

                        # Condition to display the text based on the toggle state
                        if st.session_state.get(f"show_chart_{dim}_{i}", False):
                            #dict1 = get_dict_from_df(location_sales_features_df[location_sales_features_df['sale_uid'] == 'fr_fr412030'])
                            #dict2 = get_dict_from_df(location_sales_features_df[location_sales_features_df['sale_uid'] == 'fr_fr411914'])
                            sale_uid_1 = all_top_sales_dict[dim]['sale_uid_a'].iloc[0]
                            sale_uid_2 = all_top_sales_dict[dim]['sale_uid_b'].iloc[i]
                            dict1 = get_dict_from_df(thematic_features[dim][thematic_features[dim]['sale_uid'] == sale_uid_1])
                            dict2 = get_dict_from_df(thematic_features[dim][thematic_features[dim]['sale_uid'] == sale_uid_2])
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
                            sale_name_1 = sale_uid_to_name_dict.get(sale_uid_1)
                            sale_name_2 = sale_uid_to_name_dict.get(sale_uid_2)
                            df = pd.DataFrame({
                                'Feature': list(filtered_dict1.keys()) + list(filtered_dict2.keys()),
                                'Value': list(filtered_dict1.values()) + list(filtered_dict2.values()),
                                'Sales': [sale_name_1] * len(filtered_dict1) + [sale_name_2] * len(filtered_dict2)
                            })

                            # Create horizontal bar chart with Altair
                            chart = alt.Chart(df).mark_bar().encode(
                                column=alt.Column('Sales:N', title='Sales'),  # Separate bars by Sales
                                x=alt.X(
                                    'Value:Q', 
                                    axis=alt.Axis(title='Value', values=[0, 1], format='.0f'),
                                    scale=alt.Scale(domain=[0, 1])
                                ),
                                y=alt.Y('Feature:N', axis=alt.Axis(title='Feature'), sort='-x'),
                                color=alt.Color('Sales:N', scale=alt.Scale(range=['#e74c3c', '#2874a6']),legend=None),
                                tooltip=['Feature:N', 'Value:Q', 'Sales:N']
                            ).properties(
                                title="Comparison of Features",
                                width=300,
                                height=400
                            )
                            
                            st.markdown("_Disclaimer: some informations we use such as latitude, longitude, price are not yet displayed here. Stay tuned._")

                            st.altair_chart(chart)

        st.text("\n\n")
        st.text("\n\n")

        # combine rankings for similarity plot
        combined_dim_top_sales_df = pd.concat(
            all_top_sales_dict.values(),
            ignore_index=True
        )

        st.text("\n\n\n\n")
        st.text("voila")

        # display chart rank v similarity
        display_chart_rank_v_similarity(combined_dim_top_sales_df)

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


if __name__ == "__main__":
    main()