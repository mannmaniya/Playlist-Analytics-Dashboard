# US Top 50 Playlist Performance Analytics

This repository contains a Streamlit dashboard and notebook for analyzing United States Top 50 playlist performance using historical daily playlist snapshots.

## Project Scope
- Data validation and chart integrity checks
- Playlist ranking stability and volatility analysis
- Song longevity, average rank, best rank, and trend scoring
- Artist dominance, repeat appearances, and playlist presence
- Popularity vs rank correlation and rank bucket distribution
- Content attribute analysis for explicitness, album type, duration, and album size

## Updated Deliverables
- `main.py`: Streamlit dashboard with interactive filters and analytics panels
- `eda_and_features.ipynb`: Notebook for feature engineering, validation, and summary tables
- `requirements.txt`: Updated dependencies including `numpy`

## Key Dashboard Modules
- Playlist timeline explorer
- Rank distribution and popularity scatter analysis
- Artist dominance leaderboard
- Song-level persistence and popularity leaderboards
- Explicit vs non-explicit and album vs single performance panels
- Entry/exit momentum and fast riser / slow decliner tracking

## Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the Streamlit app:
   ```bash
   streamlit run main.py
   ```

## Notes
- This app is designed for historical playlist analytics, not prediction or recommendation.
- To update the deployed Streamlit app at `https://playlist-analytics-dashboard.streamlit.app/`, push changes to the connected GitHub repository and redeploy through Streamlit Cloud.
