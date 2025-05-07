"""
Name:       Petra Radinkovic
CS230:      230-1
Data:       McDonald_s_Reviews
URL:    https://mcdonaldsreviews-fhtlremi4xwaknesr9aliq.streamlit.app/


Description:
This program explores McDonald’s customer reviews across the United States using a
real-world dataset. Users can interactively filter reviews by town, year, or keyword,
visualize data on a map colored by sentiment, and analyze patterns through charts and
summary statistics. Additional features include identifying the best and worst towns
based on ratings, and a fun tool that compares how often different words appear in reviews.

"""

import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["McDonalds Reviews Dataset","Store Locations Map","Reviews by Town","Reviews by Year","Word Game","Summary of the Dataset"])

with tab1:
    # Title and description
    st.title("McDonald's Reviews")
    st.write("Explore customer reviews and ratings from McDonald's locations across the U.S.")

    # Load the CSV file
    df = pd.read_csv("McDonald_s_Reviews.csv", encoding="latin1")

    # Show the dataset
    st.subheader("Preview of the Dataset")
    st.dataframe(df)

# [DA1] Clean the data

# Clean column names
df.columns = df.columns.str.strip().str.lower()


# Convert 'rating' to float
if "rating" in df.columns:
    df["rating"] = df["rating"].astype(str).str.extract(r"(\d)").astype(float)

# Clean "review" column by removing special symbols
if "review" in df.columns:
    df["review"] = df["review"].astype(str).str.replace(r"[^A-Za-z0-9 ]", "", regex=True)

# Convert "review_time" to year the review was sent

reviewTime = {
    "2 days ago":"2025",
    "3 days ago":"2025",
    "4 days ago":"2025",
    "5 days ago":"2025",
    "6 days ago":"2025",
    "a week ago":"2025",
    "2 weeks ago":"2025",
    "3 weeks ago":"2025",
    "4 weeks ago":"2025",
    "a month ago":"2025",
    "2 months ago":"2025",
    "3 months ago":"2025",
    "4 months ago":"2025",
    "5 months ago":"2024",
    "6 months ago":"2024",
    "7 months ago":"2024",
    "8 months ago":"2024",
    "9 months ago":"2024",
    "10 months ago":"2024",
    "11 months ago":"2024",
    "a year ago":"2024",
    "2 years ago":"2023",
    "3 years ago":"2022",
    "4 years ago":"2021",
    "5 years ago":"2020",
    "6 years ago":"2019",
    "7 years ago":"2018",
    "8 years ago":"2017",
    "9 years ago":"2016",
    "10 years ago":"2015",
    "11 years ago":"2014",
    "12 years ago":"2013",
    "13 years ago":"2012"
}

df["review_year"] = df["review_time"].map(reviewTime)


# Extract store_town from address

def extract_town(address):
    try:
        parts = address.split(",")
        if len(parts) >= 3:
            town = parts[1].strip()  # Second element = town
        elif len(parts) == 2:
            town = parts[0].strip()  # Fall back to first part
        else:
            town = ""
        town = ''.join(c for c in town if c.isalpha() or c.isspace()).strip()
        return town
    except:
        return ""

df['store_town'] = df['store_address'].apply(extract_town)

# # Show cleaned DataFrame   (I decided to not show it, but kept it in case I needed to)
# st.subheader("Cleaned Dataset")
# st.dataframe(df)

with tab2:
    # Visualisation - MAP

    st.subheader("Store Locations Map (Colored by Rating)")
    st.write(
        "Each point represents a town. The color indicates its average customer rating:\n"
        "🟢 Green – Excellent (≥ 4.0)\n"
        "🟡 Yellow – Average (3.0–3.99)\n"
        "🔴 Red – Poor (< 3.0)"
    )

    # Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Filter rows with valid data
    df_filtered = df.dropna(subset=["latitude", "longitude", "rating", "store_town"])

    # Group by town and get average rating and location
    town_avg = (
        df_filtered.groupby("store_town")
        .agg(
            avg_rating=("rating", "mean"),
            lat=("latitude", "mean"),
            lon=("longitude", "mean")
        )
        .reset_index()
    )

    town_avg["avg_rating"] = town_avg["avg_rating"].round(2)


    # Color by average rating
    def rating_color(rating):
        if rating >= 4.0:
            return [0, 200, 0]  # Green
        elif rating >= 3.0:
            return [255, 255, 0]  # Yellow
        else:
            return [255, 0, 0]


    town_avg["color"] = town_avg["avg_rating"].apply(rating_color)

    # Create PyDeck layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=town_avg,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=8000,
        pickable=True,
    )

    # View state centered on the data
    view_state = pdk.ViewState(
        latitude=town_avg["lat"].mean(),
        longitude=town_avg["lon"].mean(),
        zoom=4
    )

    # Tooltip to show average rating and town
    tooltip = {
        "html": "<b>Town:</b> {store_town}<br><b>Avg Rating:</b> {avg_rating}",
        "style": {
            "backgroundColor": "grey",
            "color": "white"
        }
    }

    # Show the map
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip
        )
    )

with tab3:
    # [DA3] Find Top largest or smallest values of a column
    # Get top 5 towns by review count
    top_towns = df["store_town"].value_counts().head(5).index

    # Filter dataset to those towns
    top_town_data = df[df["store_town"].isin(top_towns)]

    # Group by town and calculate average rating
    avg_ratings = top_town_data.groupby("store_town")["rating"].mean().sort_values(ascending=False)

    # Show bar chart
    st.subheader("Average Rating of Top 5 Most Reviewed Towns")
    st.bar_chart(avg_ratings)

    # Streamlit feature -  Dropdown to filter by town
    selected_town = st.selectbox("Select a town to view reviews", df["store_town"].dropna().unique())
    filtered = df[df["store_town"] == selected_town]
    st.dataframe(filtered[["review", "rating", "review_year"]])

    # Streamlit feature - Text input for keyword search
    keyword = st.text_input("Search for a keyword in reviews:")
    if keyword:
        matches = df[df["review"].str.contains(keyword, case=False, na=False)]
        st.write(f"Found {len(matches)} reviews containing '{keyword}'")
        st.dataframe(matches[["store_town", "review", "rating"]])

with tab4:

    # Streamlit feature - Slider to show only reviews from a certain year
    year_filter = st.slider("Show reviews from year", min_value=2013, max_value=2025, value=2025)
    filtered_by_year = df[df["review_year"] == str(year_filter)]

    st.subheader(f"Reviews from {year_filter}")
    st.dataframe(filtered_by_year[["store_town", "review", "rating"]])


    # [PY1] A function with two or more parameters
    def keyword_count(word, year="all"):
        reviews = df["review"].dropna().astype(str)
        if year != "all":
            reviews = df[df["review_year"] == str(year)]["review"].dropna().astype(str)
        count = sum(word.lower() in review.lower() for review in reviews)
        return count, len(reviews)


    st.subheader("Number of Reviews per Year")
    review_counts = df["review_year"].value_counts().sort_index()
    st.line_chart(review_counts)

with tab5:
    # Battle
    st.subheader("Which word is more common in reviews?")

    # User input
    word1 = st.text_input("Enter the first word to battle", "")
    word2 = st.text_input("Enter the second word to battle", "")
    battle_year = st.selectbox("Filter by year (optional)",
                               ["all"] + sorted(df["review_year"].dropna().unique(), reverse=True))

    # Trigger the battle when both words are provided
    if word1 and word2:
        count1, total = keyword_count(word1, battle_year)
        count2, _ = keyword_count(word2, battle_year)

        st.write(f"In {battle_year if battle_year != 'all' else 'all years'}, out of {total} reviews:")
        st.write(f" '{word1}' appeared {count1} times")
        st.write(f" '{word2}' appeared {count2} times")

        # Display the winner
        if count1 > count2:
            st.success(f" '{word1}' wins!")
        elif count2 > count1:
            st.success(f" '{word2}' wins!")
        else:
            st.info("It's a tie!")



with tab6:
    # Visualisation - histogram

    st.subheader("Rating Distribution Histogram")
    fig, ax = plt.subplots()
    ax.hist(df["rating"].dropna(), bins=5, color='skyblue', edgecolor='black')
    ax.set_title("Distribution of Ratings")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Count")
    st.pyplot(fig)


    # [DA6] Summary stats, analyze data with pivot tables
    st.subheader("Summary")

    st.write("Maximum Rating:", df["rating"].max())
    st.write("Minimum Rating:", df["rating"].min())
    st.write("Average Rating:", round(df["rating"].mean(), 2))
    st.write("Total Number of Reviews:", len(df))

    # Most common review year
    most_common_year = df["review_year"].value_counts().idxmax()
    review_count_year = df["review_year"].value_counts().max()
    st.write("Most Active Review Year:", most_common_year, f"({review_count_year} reviews)")

    # Most common word
    from collections import Counter

    words = " ".join(df["review"].dropna().astype(str).str.lower()).split()
    word_counts = Counter(words)
    common_word, count = word_counts.most_common(1)[0]
    st.write(f"Most Common Word in Reviews: '{common_word}' ({count} times)")

    # [DA7] Add/drop/select/create new/group columns
    town_avg = df.groupby("store_town")["rating"].mean()
    town_counts = df["store_town"].value_counts()
    qualified_towns = town_avg

    if not qualified_towns.empty:
        best_town = qualified_towns.idxmax()
        best_rating = qualified_towns.max()
        worst_town = qualified_towns.idxmin()
        worst_rating = qualified_towns.min()


        # [PY2] -A function that returns more than one value

        def best_and_worst_town():
            best = qualified_towns.idxmax(), qualified_towns.max()
            worst = qualified_towns.idxmin(), qualified_towns.min()
            return best, worst


        best, worst = best_and_worst_town()
        st.write(f"Best Town: {best[0]} ({round(best[1], 2)})")
        st.write(f"Worst Town: {worst[0]} ({round(worst[1], 2)})")



