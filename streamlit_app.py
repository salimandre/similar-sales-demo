import altair as alt
import pandas as pd
import streamlit as st
import numpy as np

from streamlit_app_utils import PAGE_CONFIG, DEFAULT_SELECTIONS, DATA_FILES, \
    get_utils, load_json_file, load_csv, \
    compare_features, load_data, get_selected_sale_details, display_chart_rank_v_similarity



def main():
    # Utils
    sale_url_template, extract_sale_id, display_url_html, \
    get_dict_from_df, available_sale_dimensions, available_sale_dimensions_inv, \
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

    # Adding selection box for culture choice
    selected_culture = st.selectbox(
        "culture",
        ("fr_FR", "it_IT", "es_ES", "en_GB", "nl_NL", "de_AT", "de_DE", "fr_BE", "nl_BE", "fr_CH", "de_CH"),
    )

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
        
        # Step 2: Allow users to assign weights to each selected dimension
        similarity_weights = {}
        selected_rankings_df['weighted_similarity'] = 0
        if selected_sale_dimensions:
            st.write("Assign weights to each selected dimension (sum should ideally be 1):")
            for dim in selected_sale_dimensions:
                default_weight_dim = DEFAULT_SELECTIONS.get('Weights').get(dim)
                similarity_weights[dim] = st.slider(f"{dim}", min_value=0.0, max_value=1.0, value=default_weight_dim, step=0.05)
                dim_sim_col = available_sale_dimensions.get(dim) + '__similarity'
                selected_rankings_df['weighted_similarity'] += similarity_weights[dim] * selected_rankings_df[dim_sim_col]

        # Get the weighted global ranking
        global_top_sales_df = selected_rankings_df.sort_values(by='weighted_similarity', ascending=False).iloc[min_rank-1:max_rank]
        global_top_sales_df['weighted_similarity_rank'] = global_top_sales_df['weighted_similarity'].rank(method='first', ascending=False).astype(int)
        
        global_top_sales_df.drop(columns=['similarity', 'similarity_rank'], inplace=True)
        global_top_sales_df = global_top_sales_df.rename(columns={"weighted_similarity_rank": "rank", "weighted_similarity": "similarity"})

        global_top_sales_df['sale_url'] = [display_url_html(sale_url_template.format(insert_sale_id=extract_sale_id(s_uid))) for s_uid in global_top_sales_df["sale_uid_b"]]

        # Display dimension
        st.text("\n\n")
        st.markdown(f"### {available_sale_dimensions_emojis.get('Global')} Top Results")

        for i in range(max_rank - min_rank + 1):

            # Prepare offer
            offer = get_dict_from_df(global_top_sales_df.iloc[[i]])

            with st.container():
                # Display Offer Details
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                col1.markdown(f"**#{i+1}**")
                col2.markdown(f"**Similarity:** {offer['similarity']:.3f}")
                col3.markdown(f"{offer['sale_url']}", unsafe_allow_html=True)

                # Add a button in col4 to toggle chart display
                if col4.button("Explain", key=f"toggle_global_{i}"):
                    # Toggle the display state in session state
                    key = f"show_chart_global_{i}"
                    if key not in st.session_state:
                        st.session_state[key] = True
                    else:
                        st.session_state[key] = not st.session_state[key]

                # Condition to display the text based on the toggle state
                if st.session_state.get(f"show_chart_global_{i}", False):
                    sale_uid_1 = global_top_sales_df['sale_uid_a'].iloc[0]
                    sale_uid_2 = global_top_sales_df['sale_uid_b'].iloc[i]
                    dict2 = get_dict_from_df(global_top_sales_df[global_top_sales_df['sale_uid_b'] == sale_uid_2])
                    #st.write(dict2)
                    
                    df = pd.DataFrame(
                        [{'Dimension': k.split('__')[0], 'Type': 'Raw', 'Similarity': dict2[k]} for k in dict2 if k.endswith("__similarity")] \
                        + [{'Dimension': k.split('__')[0], 'Type': 'Weighted', 'Similarity': dict2[k]*similarity_weights[available_sale_dimensions_inv.get(k.split('__')[0])]} for k in dict2 if k.endswith("__similarity")]
                    )

                    df['Dimension_Type'] = np.where(df['Type'] == 'Raw', df['Dimension'], df['Dimension'] + ' ')
                    df = df.sort_values(by='Dimension_Type', ascending=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    chart = alt.Chart(df).mark_bar().encode(
                        x=alt.X('Dimension_Type:N', axis=alt.Axis(title='Dimension'), sort=None),
                        y=alt.Y('Similarity:Q', axis=alt.Axis(title='Similarity')),
                        color='Type:N'
                    ).properties(
                        width=550,
                        height=450
                    )

                    chart

                    if st.button("Comparison of Features", key=f"sub_toggle_global_{i}"):
                        # Toggle the display state in session state
                        key = f"show_sub_chart_global_{i}"
                        if key not in st.session_state:
                            st.session_state[key] = True
                        else:
                            st.session_state[key] = not st.session_state[key]
                    
                    # Condition to display the text based on the toggle state
                    if st.session_state.get(f"show_sub_chart_global_{i}", False):                            
                        for dim in available_sale_dimensions:
                            dict1 = get_dict_from_df(thematic_features[dim][thematic_features[dim]['sale_uid'] == sale_uid_1])
                            dict2 = get_dict_from_df(thematic_features[dim][thematic_features[dim]['sale_uid'] == sale_uid_2])

                            # Display table of feature comparison for dim
                            st.markdown(f"###### {dim}")
                            sale_name_1 = sale_uid_to_name_dict.get(sale_uid_1)
                            sale_name_2 = sale_uid_to_name_dict.get(sale_uid_2)
                            features_1 = {k: v for k, v in dict1.items() if k not in ('sale_uid')}
                            features_2 = {k: v for k, v in dict2.items() if k not in ('sale_uid')}
                            df1 = pd.DataFrame(list(features_1.items()), columns=['Feature', sale_name_1]).astype(str)
                            df2 = pd.DataFrame(list(features_2.items()), columns=['Feature', sale_name_2]).astype(str)
                            df = pd.merge(df1, df2, on='Feature')

                            def style_specific_cell(row):
                                # Initialize an empty list to store styles
                                styles = ['']

                                # Apply color based on the value of each column
                                if row[sale_name_1] != '0':
                                    styles.append('background-color: #ffcccc')  # Red color for Hotel 1 if value is not '0'
                                else:
                                    styles.append('')  # No styling if the value is '0'
                                
                                if row[sale_name_2] != '0':
                                    styles.append('background-color: #ccccff')  # Blue color for Hotel 2 if value is not '0'
                                else:
                                    styles.append('')  # No styling if the value is '0'

                                return styles

                            styled_df = df.style.apply(style_specific_cell, axis=1)
                            st.dataframe(styled_df)


        # display chart rank v similarity
        st.markdown("<br><br>", unsafe_allow_html=True)
        global_top_sales_df['dimension'] = 'global'
        display_chart_rank_v_similarity(global_top_sales_df)


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
                            sale_uid_1 = all_top_sales_dict[dim]['sale_uid_a'].iloc[0]
                            sale_uid_2 = all_top_sales_dict[dim]['sale_uid_b'].iloc[i]
                            dict1 = get_dict_from_df(thematic_features[dim][thematic_features[dim]['sale_uid'] == sale_uid_1])
                            dict2 = get_dict_from_df(thematic_features[dim][thematic_features[dim]['sale_uid'] == sale_uid_2])
                            common_features, different_features = compare_features(dict1, dict2)
                            #st.write(dict2) TO REMOVE
                            # Display table of feature comparison for dim
                            st.markdown("###### Comparison of Features")
                            sale_name_1 = sale_uid_to_name_dict.get(sale_uid_1)
                            sale_name_2 = sale_uid_to_name_dict.get(sale_uid_2)
                            features_1 = {k: v for k, v in dict1.items() if k not in ('sale_uid')}
                            features_2 = {k: v for k, v in dict2.items() if k not in ('sale_uid')}
                            df1 = pd.DataFrame(list(features_1.items()), columns=['Feature', sale_name_1]).astype(str)
                            df2 = pd.DataFrame(list(features_2.items()), columns=['Feature', sale_name_2]).astype(str)
                            df = pd.merge(df1, df2, on='Feature')

                            def style_specific_cell(row):
                                # Initialize an empty list to store styles
                                styles = ['']

                                # Apply color based on the value of each column
                                if row[sale_name_1] != '0':
                                    styles.append('background-color: #ffcccc')  # Red color for Hotel 1 if value is not '0'
                                else:
                                    styles.append('')  # No styling if the value is '0'
                                
                                if row[sale_name_2] != '0':
                                    styles.append('background-color: #ccccff')  # Blue color for Hotel 2 if value is not '0'
                                else:
                                    styles.append('')  # No styling if the value is '0'

                                return styles

                            styled_df = df.style.apply(style_specific_cell, axis=1)
                            st.dataframe(styled_df)

        st.markdown("<br><br>", unsafe_allow_html=True)

        # combine rankings for similarity plot
        combined_dim_top_sales_df = pd.concat(
            all_top_sales_dict.values(),
            ignore_index=True
        )

        # display chart rank v similarity
        display_chart_rank_v_similarity(combined_dim_top_sales_df)

    # Footer
    st.markdown("---")  # Horizontal line for separation
    st.markdown(
        """
        <div style='text-align: center;'>
            Made with 💖 by <strong>DATA</strong>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

