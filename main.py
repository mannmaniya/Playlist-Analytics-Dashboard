import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="US Top 50 Playlist Performance", layout="wide")

# --- 2. DATA LOADING & FEATURE ENGINEERING ---
@st.cache_data
def load_data():
    df = pd.read_csv('Atlantic_United_States.csv')
    df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
    df['duration_min'] = df['duration_ms'] / 60000
    df['artist'] = df['artist'].astype(str).str.strip()
    df['song'] = df['song'].astype(str).str.strip()
    df['album_type'] = df['album_type'].astype(str).str.title()
    df['is_explicit'] = df['is_explicit'].astype(str).str.upper()
    df['rank_bucket'] = pd.cut(df['position'], bins=[0, 10, 20, 50], labels=['Top 10', 'Top 20', 'Top 50'])
    df = df.sort_values(['song', 'date']).reset_index(drop=True)
    df['pop_trend_7d'] = df.groupby('song')['popularity'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
    df['rank_change'] = df.groupby('song')['position'].diff().fillna(0)
    df['day_on_chart'] = df.groupby(['song', 'artist'])['date'].transform('count')
    return df

@st.cache_data
def compute_metrics(df):
    song_metrics = df.groupby(['song', 'artist']).agg(
        days_on_chart=('date', 'count'),
        first_date=('date', 'min'),
        last_date=('date', 'max'),
        avg_rank=('position', 'mean'),
        best_rank=('position', 'min'),
        rank_volatility=('position', 'std'),
        avg_popularity=('popularity', 'mean'),
        popularity_volatility=('popularity', 'std')
    ).reset_index()
    song_metrics['rank_volatility'] = song_metrics['rank_volatility'].fillna(0)
    song_metrics['popularity_volatility'] = song_metrics['popularity_volatility'].fillna(0)
    song_metrics['chart_span_days'] = (song_metrics['last_date'] - song_metrics['first_date']).dt.days + 1

    artist_metrics = df.groupby('artist').agg(
        unique_songs=('song', 'nunique'),
        total_chart_days=('date', 'count'),
        avg_rank=('position', 'mean'),
        best_rank=('position', 'min'),
        avg_popularity=('popularity', 'mean')
    ).reset_index().sort_values('total_chart_days', ascending=False)

    validation = {
        'missing_values': int(df.isna().sum().sum()),
        'invalid_rank_rows': int(df[~df['position'].between(1, 50)].shape[0]),
        'duplicate_song_date': int(df.duplicated(subset=['song', 'artist', 'date']).sum())
    }
    return song_metrics, artist_metrics, validation

@st.cache_data
def top_movers(df, metric='rank_change', top_n=10):
    movers = (
        df[df['date'] > df['date'].min()]
          .sort_values(metric)
          .head(top_n)
          .drop_duplicates(subset=['song', 'artist', 'date'])
    )
    return movers


df = load_data()

# --- 3. DASHBOARD FILTERS ---
st.sidebar.header("Filter Controls")

date_range = st.sidebar.date_input(
    "Date Range",
    [df['date'].min().date(), df['date'].max().date()],
    min_value=df['date'].min().date(),
    max_value=df['date'].max().date()
)
artist_options = sorted(df['artist'].unique())
selected_artists = st.sidebar.multiselect("Artist(s)", options=artist_options, default=artist_options)

song_options = sorted(df['song'].unique())
selected_songs = st.sidebar.multiselect("Song(s)", options=song_options, default=song_options)

album_options = sorted(df['album_type'].unique())
selected_album_types = st.sidebar.multiselect("Album Type", options=album_options, default=album_options)

explicit_options = ['TRUE', 'FALSE']
selected_explicit = st.sidebar.multiselect("Explicit content", options=explicit_options, default=explicit_options)

rank_min, rank_max = st.sidebar.slider(
    "Rank range",
    min_value=int(df['position'].min()),
    max_value=int(df['position'].max()),
    value=(int(df['position'].min()), int(df['position'].max())),
    step=1
)

show_validation = st.sidebar.checkbox("Show data validation summary", value=True)

filtered_df = df[
    (df['date'].dt.date >= date_range[0]) &
    (df['date'].dt.date <= date_range[1]) &
    (df['artist'].isin(selected_artists)) &
    (df['song'].isin(selected_songs)) &
    (df['album_type'].isin(selected_album_types)) &
    (df['is_explicit'].isin(selected_explicit)) &
    (df['position'].between(rank_min, rank_max))
]

song_metrics, artist_metrics, validation = compute_metrics(filtered_df)

# --- 4. MAIN CONTENT ---
st.title("United States Top 50 Playlist Performance")
st.markdown(
    "Analyze chart stability, song longevity, artist dominance, popularity trend scores, and content attribute performance for U.S. Top 50 streaming data."
)

if filtered_df.empty:
    st.warning("No matching records found. Adjust the filters to explore more of the playlist data.")
    st.stop()

# Validation summary
if show_validation:
    st.subheader("Data Validation & Quality Checks")
    val_cols = st.columns(3)
    val_cols[0].metric("Missing values", validation['missing_values'])
    val_cols[1].metric("Invalid rank rows", validation['invalid_rank_rows'])
    val_cols[2].metric("Duplicate song-date records", validation['duplicate_song_date'])

# KPI row
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
longest_chart = song_metrics.loc[song_metrics['days_on_chart'].idxmax()]
kpi1.metric("Unique Tracks", filtered_df['song'].nunique())
kpi2.metric("Unique Artists", filtered_df['artist'].nunique())
kpi3.metric("Avg Popularity", round(filtered_df['popularity'].mean(), 1))
kpi4.metric("Avg Rank", round(filtered_df['position'].mean(), 1))
kpi5.metric("Top song chart days", int(longest_chart['days_on_chart']))

st.divider()

# Ranking and popularity overview
st.subheader("Playlist Ranking & Popularity Analytics")
row1, row2 = st.columns((2, 1))
with row1:
    fig_rank_dist = px.histogram(
        filtered_df,
        x='position',
        nbins=10,
        title='Rank distribution across filtered song set',
        labels={'position': 'Chart Rank'}
    )
    fig_rank_dist.update_xaxes(autorange='reversed')
    st.plotly_chart(fig_rank_dist, use_container_width=True)

    fig_pop_rank = px.scatter(
        filtered_df,
        x='popularity',
        y='position',
        color='rank_bucket',
        hover_data=['song', 'artist'],
        title='Popularity vs chart rank',
        labels={'position': 'Rank', 'popularity': 'Popularity Score'}
    )
    fig_pop_rank.update_yaxes(autorange='reversed')
    st.plotly_chart(fig_pop_rank, use_container_width=True)

with row2:
    st.metric("Explicit share", f"{round((filtered_df['is_explicit'] == 'TRUE').mean() * 100, 1)}%")
    st.metric("Avg duration", f"{round(filtered_df['duration_min'].mean(), 2)} min")
    st.metric("Avg rank volatility", round(song_metrics['rank_volatility'].mean(), 2))
    st.metric("Avg popularity trend", round(filtered_df['pop_trend_7d'].mean(), 1))

st.divider()

# Timeline explorer
st.subheader("Song Ranking Timeline Explorer")

top_songs = song_metrics.sort_values('avg_rank').head(15)['song'].unique()
selected_timeline_songs = st.multiselect(
    "Select songs to view rank timeline",
    options=top_songs,
    default=list(top_songs[:5])
)
if selected_timeline_songs:
    timeline_data = filtered_df[filtered_df['song'].isin(selected_timeline_songs)]
    fig_timeline = px.line(
        timeline_data,
        x='date',
        y='position',
        color='song',
        line_shape='spline',
        markers=True,
        title='Selected song ranking trajectories'
    )
    fig_timeline.update_yaxes(autorange='reversed', dtick=1)
    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.info("Choose one or more songs from the selector to display ranking timelines.")

st.divider()

# Song performance and trend metrics
st.subheader("Song-Level Performance Metrics")
longest_songs = song_metrics.sort_values(['days_on_chart', 'avg_rank']).head(10)
popular_songs = song_metrics.sort_values(['avg_popularity', 'avg_rank'], ascending=[False, True]).head(10)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Top songs by chart persistence**")
    st.dataframe(longest_songs[['song', 'artist', 'days_on_chart', 'avg_rank', 'best_rank', 'rank_volatility']].reset_index(drop=True))
with col2:
    st.markdown("**Top songs by avg popularity**")
    st.dataframe(popular_songs[['song', 'artist', 'avg_popularity', 'days_on_chart', 'avg_rank']].reset_index(drop=True))

st.divider()

# Artist dominance
st.subheader("Artist Dominance & Repeat Appearances")
artist_top = artist_metrics.head(12)
fig_artist = px.bar(
    artist_top,
    x='total_chart_days',
    y='artist',
    orientation='h',
    color='unique_songs',
    title='Top artists by chart presence',
    labels={'total_chart_days': 'Total chart days', 'artist': 'Artist'}
)
fig_artist.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_artist, use_container_width=True)

st.divider()

# Content attribute analysis
st.subheader("Content Attributes and Popularity")
rowA, rowB = st.columns(2)
with rowA:
    explicit_summary = filtered_df.groupby('is_explicit')['popularity'].agg(['mean', 'count']).reset_index()
    fig_explicit = px.bar(explicit_summary, x='is_explicit', y='mean', color='is_explicit', title='Average popularity by explicit flag')
    st.plotly_chart(fig_explicit, use_container_width=True)
    album_summary = filtered_df.groupby('album_type')['popularity'].agg(['mean', 'count']).reset_index()
    fig_album = px.bar(album_summary, x='album_type', y='mean', color='album_type', title='Average popularity by album type')
    st.plotly_chart(fig_album, use_container_width=True)

with rowB:
    fig_duration = px.scatter(
        filtered_df,
        x='duration_min',
        y='popularity',
        color='rank_bucket',
        title='Duration vs popularity score'
    )
    st.plotly_chart(fig_duration, use_container_width=True)
    fig_tracks = px.scatter(
        filtered_df,
        x='total_tracks',
        y='popularity',
        color='album_type',
        title='Album size vs song popularity'
    )
    st.plotly_chart(fig_tracks, use_container_width=True)

st.divider()

# Fast risers and slow decliners
st.subheader("Entry/Exit Movement and Chart Momentum")
fast_risers = top_movers(filtered_df, metric='rank_change', top_n=10)
slow_decliners = top_movers(filtered_df, metric='rank_change', top_n=10).sort_values('rank_change', ascending=False)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Fast risers**")
    st.dataframe(fast_risers[['date', 'song', 'artist', 'position', 'rank_change']].head(10).reset_index(drop=True))
with col2:
    st.markdown("**Slow decliners**")
    st.dataframe(slow_decliners[['date', 'song', 'artist', 'position', 'rank_change']].head(10).reset_index(drop=True))

st.markdown("---")
st.markdown(
    "**Project scope:** This dashboard supports playlist timeline exploration, rank trend analysis, artist dominance overview, popularity vs rank correlation, explicit vs non-explicit performance, and content attribute benchmarking."
)
