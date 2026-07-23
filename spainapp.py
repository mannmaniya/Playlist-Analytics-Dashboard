import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Spain Top 50 Lifecycle Analytics", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("Atlantic_Spain.csv")
    df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
    df['track_id'] = df['song'] + " - " + df['artist']
    return df

df = load_data()

st.title("🎶 Spain Top 50: Content Maturity & Lifecycle Dashboard")
st.markdown("Intelligence for Atlantic Recording Corporation release optimization.")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Controls")
min_date, max_date = df['date'].min(), df['date'].max()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date])

explicit_filter = st.sidebar.selectbox("Content Maturity", ["All", "Explicit", "Clean"])
album_filter = st.sidebar.selectbox("Release Type", ["All", "Single", "Album"])

# Apply Filters
filtered_df = df[(df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])]

if explicit_filter == "Explicit":
    filtered_df = filtered_df[filtered_df['is_explicit'] == True]
elif explicit_filter == "Clean":
    filtered_df = filtered_df[filtered_df['is_explicit'] == False]

if album_filter != "All":
    filtered_df = filtered_df[filtered_df['album_type'] == album_filter.lower()]

# --- KPIS ---
st.header("Executive KPIs")
col1, col2, col3, col4 = st.columns(4)

total_unique_songs = filtered_df['track_id'].nunique()
avg_popularity = filtered_df['popularity'].mean()

col1.metric("Unique Tracks in Period", total_unique_songs)
col2.metric("Average Popularity", f"{avg_popularity:.1f}")

# --- VISUALIZATIONS ---
st.markdown("---")
st.header("Playlist Churn & Rotation")

# Churn Chart
daily_churn = filtered_df.groupby('date')['track_id'].nunique().reset_index()
fig_churn = px.line(daily_churn, x='date', y='track_id', title="Daily Unique Track Count (Volatility)")
st.plotly_chart(fig_churn, use_container_width=True)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Explicit vs Clean Distribution")
    fig_pie = px.pie(filtered_df, names='is_explicit', title="Explicit Content Share")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    st.subheader("Single vs Album Track Performance")
    fig_bar = px.histogram(filtered_df, x='album_type', color='album_type', title="Frequency by Album Type")
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.header("Song Lifecycle Timeline Explorer")
# Allow user to pick a specific track to see its lifecycle
top_songs = filtered_df['track_id'].value_counts().head(10).index.tolist()
selected_song = st.selectbox("Select a Track to View Position Lifecycle:", top_songs)

song_data = filtered_df[filtered_df['track_id'] == selected_song]
fig_lifecycle = px.line(song_data, x='date', y='position', title=f"Ranking Trajectory: {selected_song}")
fig_lifecycle.update_yaxes(autorange="reversed") # Reverse Y axis so Rank 1 is at the top
st.plotly_chart(fig_lifecycle, use_container_width=True)