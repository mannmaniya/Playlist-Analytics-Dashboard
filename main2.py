import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv("Atlantic_Spain.csv")

# Convert date string to datetime (format is DD-MM-YYYY based on the data)
df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')

# Normalize text columns to avoid case-sensitivity issues
df['song'] = df['song'].str.strip().str.lower()
df['artist'] = df['artist'].str.strip().str.lower()

# Validate: Check if there are exactly 50 entries per day
daily_counts = df.groupby('date').size()
missing_days = daily_counts[daily_counts != 50]
if not missing_days.empty:
    print(f"Warning: The following dates do not have exactly 50 tracks:\n{missing_days}")

# Create a unique identifier just in case different artists have the same song title
df['track_id'] = df['song'] + " - " + df['artist']

lifecycle_df = df.groupby('track_id').agg(
    entry_date=('date', 'min'),
    exit_date=('date', 'max'),
    total_days_on_playlist=('date', 'nunique'),
    peak_position=('position', 'min'),
    avg_popularity=('popularity', 'mean'),
    is_explicit=('is_explicit', 'first'),
    album_type=('album_type', 'first'),
    duration_ms=('duration_ms', 'first')
).reset_index()

# Calculate Time to Peak (Days from entry to first time hitting peak position)
peak_dates = df.loc[df.groupby('track_id')['position'].idxmin()][['track_id', 'date']]
peak_dates.rename(columns={'date': 'peak_date'}, inplace=True)

lifecycle_df = lifecycle_df.merge(peak_dates, on='track_id')
lifecycle_df['time_to_peak_days'] = (lifecycle_df['peak_date'] - lifecycle_df['entry_date']).dt.days

def classify_stage(row, entry_date):
    days_alive = (row['date'] - entry_date).days
    
    if days_alive <= 7:
        return 'New Entry'
    elif row['position'] <= 10:
        return 'Peak Phase'
    # For a robust model, you'd calculate weekly rank delta. 
    # Here is a simplified baseline:
    elif row['position'] > 10 and row['position'] <= 30:
        return 'Mature Phase'
    else:
        return 'Decline Phase'

# Map entry dates back to the daily dataframe
df = df.merge(lifecycle_df[['track_id', 'entry_date']], on='track_id')
df['lifecycle_stage'] = df.apply(lambda x: classify_stage(x, x['entry_date']), axis=1)

# Daily new entries (tracks where 'date' == 'entry_date')
df['is_new_entry'] = df['date'] == df['entry_date']
daily_rotation = df.groupby('date')['is_new_entry'].sum().reset_index()
daily_rotation.rename(columns={'is_new_entry': 'new_entries_count'}, inplace=True)

# Average Churn Rate (New entries per day / 50 total spots)
daily_rotation['churn_rate_%'] = (daily_rotation['new_entries_count'] / 50) * 100
average_churn = daily_rotation['churn_rate_%'].mean()
print(f"Average Daily Playlist Churn: {average_churn:.2f}%")

# 1. Average Days on Playlist
avg_days = lifecycle_df['total_days_on_playlist'].mean()

# 2. Entry-to-Peak Time
avg_time_to_peak = lifecycle_df['time_to_peak_days'].mean()

# 3. Explicit Content Lifecycle Score (Compare explicit vs clean longevity)
explicit_longevity = lifecycle_df[lifecycle_df['is_explicit'] == True]['total_days_on_playlist'].mean()
clean_longevity = lifecycle_df[lifecycle_df['is_explicit'] == False]['total_days_on_playlist'].mean()

# 4. Single vs Album Longevity Ratio
single_longevity = lifecycle_df[lifecycle_df['album_type'] == 'single']['total_days_on_playlist'].mean()
album_longevity = lifecycle_df[lifecycle_df['album_type'] == 'album']['total_days_on_playlist'].mean()
longevity_ratio = single_longevity / album_longevity if album_longevity > 0 else 0