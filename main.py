import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="US Top 50 Song Trend Analytics", layout="wide")

# --- 2. DATA LOADING & CACHING ---
# Using @st.cache_data prevents the app from reloading the CSV every time a user clicks a button
@st.cache_data
def load_data():
    df = pd.read_csv('Atlantic_United_States.csv')
    df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
    df['duration_min'] = df['duration_ms'] / 60000
    return df

df = load_data()

# --- 3. SIDEBAR FILTERS ---
st.sidebar.title("Dashboard Filters")

# Artist Filter
selected_artists = st.sidebar.multiselect("Select Artist(s):", options=df['artist'].unique())

# Date Filter
min_date = df['date'].min().date()
max_date = df['date'].max().date()
start_date, end_date = st.sidebar.date_input("Select Date Range:", [min_date, max_date])

# Rank chart controls
top_n = st.sidebar.slider("Top songs to show in rank timeline", min_value=5, max_value=20, value=10, step=1)

# Filter the dataframe based on selections
filtered_df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
if selected_artists:
    filtered_df = filtered_df[filtered_df['artist'].isin(selected_artists)]


# --- 4. MAIN DASHBOARD ---
st.title("United States Top 50 Playlist Performance and Song Popularity Trend Analysis")
st.markdown("Tracking ranking stability, artist dominance, and longevity for strategic release planning.")

if filtered_df.empty:
    st.warning("No data matches this filter selection. Please choose a wider date range or different artist(s).")
else:
    # KPI ROW
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Unique Tracks", filtered_df['song'].nunique())
    col2.metric("Unique Artists", filtered_df['artist'].nunique())
    col3.metric("Avg Popularity Score", round(filtered_df['popularity'].mean(), 1))
    col4.metric("Avg Track Duration", f"{round(filtered_df['duration_min'].mean(), 2)} min")

    st.divider()

    # FULL WIDTH ROW: Ranking Timeline
    st.subheader("Playlist Rank Movement Over Time")
    top_songs = (filtered_df.groupby('song')['position']
                           .mean()
                           .reset_index()
                           .sort_values('position')
                           .head(top_n)['song'])
    timeline_df = filtered_df[filtered_df['song'].isin(top_songs)]
    fig_timeline = px.line(
        timeline_df,
        x='date',
        y='position',
        color='song',
        line_shape='spline',
        markers=True,
        title=f"Rank movement for top {top_n} songs by average chart position"
    )
    fig_timeline.update_yaxes(autorange='reversed', tickmode='linear', dtick=1)
    fig_timeline.update_layout(legend_title_text='Song', legend=dict(yanchor='top', y=0.99, xanchor='left', x=1.02))
    st.plotly_chart(fig_timeline, use_container_width=True)

    # SPLIT COLUMNS: Deep Dive Analytics
    colA, colB = st.columns(2)

    with colA:
        st.subheader("Explicit vs. Clean Popularity")
        explicit_stats = filtered_df.groupby('is_explicit')['popularity'].mean().reset_index()
        fig_explicit = px.bar(explicit_stats, x='is_explicit', y='popularity', color='is_explicit')
        st.plotly_chart(fig_explicit, use_container_width=True)

with colB:
    st.subheader("Album Tracks vs. Singles")
    album_stats = filtered_df.groupby('album_type')['popularity'].mean().reset_index()
    fig_album = px.bar(album_stats, x='album_type', y='popularity', color='album_type')
    st.plotly_chart(fig_album, use_container_width=True)
    