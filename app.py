import streamlit as st
import pandas as pd
import numpy as np

# --- Page config ---
st.set_page_config(page_title="FC26 Career Mode Player Finder", layout="wide")
st.title("🎮 FC26 Career Mode Player Finder")
st.markdown("Filter players by position, stats, age, skill moves, weak foot, and more.")

# --- Load CSV ---
@st.cache_data
def load_data():
    df = pd.read_csv("FC26players.csv", header=0)

    # Clean column names
    df.columns = [c.strip().lower().replace(" ", "") for c in df.columns]

    # Convert numeric columns safely
    numeric_cols = [
        "overall", "potential", "age", "pace", "shooting", "passing", "dribbling", 
        "defending", "physic", "crossing", "finishing", "headingaccuracy", 
        "shortpassing", "volleys", "curve", "freekick", "longpassing", "ballcontrol", 
        "acceleration", "sprintspeed", "agility", "reactions", "balance", "shotpower", 
        "jumping", "stamina", "strength", "longshots", "aggression", "interceptions",
        "attackpositioning", "vision", "penalties", "composure", "markingawareness", 
        "standingtackle", "slidingtackle", "diving", "handling", "kicking", 
        "gkpositioning", "reflexes", "speed", "skillmoves", "weakfoot"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Convert height from cm to feet/inches and replace the column
    if "height" in df.columns:
        def cm_to_feet_inches(cm):
            feet = int(cm // 30.48)
            inches = int(round((cm / 2.54) % 12))
            return f"{feet}'{inches}"
        df["height"] = df["height"].apply(lambda x: cm_to_feet_inches(x) if pd.notna(x) else "")

    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filter Players")

# --- Position Filter ---
if "positions" in df.columns:
    all_positions = sorted({pos.strip() for positions in df["positions"].dropna() for pos in positions.split(",")})
    selected_positions = st.sidebar.multiselect("Position(s)", all_positions)
else:
    selected_positions = []

# --- Collapsible Stat Filters ---
categories = {
    "Pace": ["pace", "acceleration", "sprintspeed", "speed"],
    "Shooting": ["shooting", "finishing", "longshots", "volleys", "shotpower", "curve", "freekick", "headingaccuracy"],
    "Passing": ["passing", "shortpassing", "longpassing", "vision", "crossing"],
    "Dribbling / Skill": ["dribbling", "ballcontrol", "agility", "balance", "reactions", "skillmoves"],
    "Defending": ["defending", "markingawareness", "standingtackle", "slidingtackle", "interceptions", "attackpositioning", "aggression"],
    "Goalkeeping": ["diving", "handling", "kicking", "reflexes", "gkpositioning"],
    "Physical / Power": ["physic", "stamina", "strength", "jumping"],
    "Composure / Mentality": ["composure", "penalties"]
}

numeric_filters = {}
categorical_filters = {}

# Numeric filters inside collapsible sections
for cat, cols in categories.items():
    with st.sidebar.expander(cat, expanded=False):
        for col in cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                min_val = int(df[col].min())
                max_val = int(df[col].max())
                numeric_filters[col] = st.slider(f"{col.replace('_', ' ').title()}", min_val, max_val, (min_val, max_val))

# Age filter
if "age" in df.columns:
    min_age = int(df["age"].min())
    max_age = int(df["age"].max())
    numeric_filters["age"] = st.sidebar.slider("Age", min_age, max_age, (min_age, max_age))

# Categorical filters
for col in ["skillmoves", "weakfoot", "preferredfoot"]:
    if col in df.columns:
        options = sorted(df[col].dropna().unique())
        categorical_filters[col] = st.sidebar.multiselect(col.replace("_"," ").title(), options)

# --- Apply Filters ---
filtered = df.copy()

# Numeric filters
for col, (min_val, max_val) in numeric_filters.items():
    filtered = filtered[(filtered[col] >= min_val) & (filtered[col] <= max_val)]

# Categorical filters
for col, selected in categorical_filters.items():
    if selected:
        filtered = filtered[filtered[col].isin(selected)]

# Position filter
if selected_positions:
    def has_position(player_positions):
        if pd.isna(player_positions):
            return False
        player_pos_list = [pos.strip() for pos in player_positions.split(",")]
        return any(pos in player_pos_list for pos in selected_positions)
    filtered = filtered[filtered["positions"].apply(has_position)]

# Format value and wage
if "value" in filtered.columns:
    filtered["value"] = filtered["value"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")
if "wage" in filtered.columns:
    filtered["wage"] = filtered["wage"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")

# --- Similar Players Section ---
st.header("🔍 Find Similar Players (Optional)")

find_similar = st.checkbox("Enable similar player search")

if find_similar:
    # Top N stats to compare
    top_n = st.slider("Number of top stats to compare", 3, 5, 3)
    leeway = st.slider("Leeway for stat difference", 0, 20, 5)

    # Select a player
    target_player_name = st.selectbox("Select a player to find similar players:", df["shortname"].unique())
    target_row = df[df["shortname"] == target_player_name].iloc[0]

    # Define stat columns (all numeric except non-stats)
    non_stat_cols = [
        "shortname", "longname", "positions", "value", "wage", "age", "dob", "league", "club",
        "nationality", "preferredfoot", "weakfoot", "skillmoves", "releaseclause", "playertraits", "height"
    ]
    stat_columns = [col for col in df.columns if col not in non_stat_cols and pd.api.types.is_numeric_dtype(df[col])]
    target_stats = pd.to_numeric(target_row[stat_columns], errors='coerce').fillna(0)

    # Top N stats
    top_stats = target_stats.nlargest(top_n).index.tolist()
    st.write("Comparing using these top stats:", top_stats)

    # Position filter for target
    target_positions = [p.strip() for p in str(target_row["positions"]).split(",")]

    # Optional age filter
    min_age_sim = int(df["age"].min())
    max_age_sim = int(df["age"].max())
    age_range_sim = st.slider("Filter similar players by age", min_age_sim, max_age_sim, (min_age_sim, max_age_sim))

    # Similarity function
    def similarity_score(row):
        diff_sum = 0
        for stat in top_stats:
            if pd.isna(row[stat]):
                return np.inf
            if abs(row[stat] - target_row[stat]) > leeway:
                return np.inf
            diff_sum += abs(row[stat] - target_row[stat])
        return diff_sum

    df["similarity"] = df.apply(similarity_score, axis=1)
    similar_players = df[(df["similarity"] != np.inf) & (df["shortname"] != target_player_name)]
    similar_players = similar_players[similar_players["positions"].apply(lambda x: any(tp in x for tp in target_positions))]
    similar_players = similar_players[
        (similar_players["age"] >= age_range_sim[0]) &
        (similar_players["age"] <= age_range_sim[1])
    ]
    similar_players = similar_players.sort_values("similarity", ascending=True)

    # Format value and wage
    similar_players["value"] = similar_players["value"].apply(lambda x: f"{int(x):,}")
    similar_players["wage"] = similar_players["wage"].apply(lambda x: f"{int(x):,}")

    st.subheader("Closest Matches")
    st.dataframe(similar_players)

# --- Display filtered players ---
st.subheader(f"{len(filtered)} players found")
st.dataframe(filtered)

# Download CSV
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered players as CSV",
    data=csv,
    file_name="filtered_players.csv",
    mime="text/csv"
)
