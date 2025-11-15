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

    # -------------------------------
    # HEIGHT → FEET + INCHES
    # -------------------------------
    def cm_to_feet_inches(cm):
        if pd.isna(cm):
            return ""
        total_inches = cm / 2.54
        feet = int(total_inches // 12)
        inches = int(round(total_inches % 12))
        return f"{feet}'{inches}"

    if "height" in df.columns:
        df["heightft"] = df["height"].apply(cm_to_feet_inches)

    # Convert numeric columns safely
    numeric_cols = [
        "overall", "potential", "age", "pace", "shooting", "passing", "dribbling",
        "defending", "physic", "crossing", "finishing", "headingaccuracy",
        "shortpassing", "volleys", "curve", "freekick", "longpassing", "ballcontrol",
        "acceleration", "sprintspeed", "agility", "reactions", "balance", "shotpower",
        "jumping", "stamina", "strength", "longshots", "aggression", "interceptions",
        "attackpositioning", "vision", "penalties", "composure", "markingawareness",
        "standingtackle", "slidingtackle", "diving", "handling", "kicking",
        "gkpositioning", "reflexes", "speed"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    return df

df = load_data()

# --- HEIGHT CONVERSION (replace cm column with ft/in column) ---

def cm_to_feet_inches(cm):
    try:
        cm = float(cm)
        total_inches = cm / 2.54
        feet = int(total_inches // 12)
        inches = int(round(total_inches % 12))
        return f"{feet}'{inches}"
    except:
        return "N/A"

# Convert existing height cm column
df["height"] = df["height"].apply(cm_to_feet_inches)

# Move converted height column to appear after 'dob'
cols = list(df.columns)

# Remove height from current position
cols.remove("height")

# Insert height right after dob
dob_index = cols.index("dob")
cols.insert(dob_index + 1, "height")

# Reassign the ordered dataframe
df = df[cols]


# --- Sidebar Filters ---
st.sidebar.header("Filter Players")

# --- Position Filter ---
if "positions" in df.columns:
    all_positions = sorted({pos.strip() for positions in df["positions"].dropna()
                            for pos in positions.split(",")})
    selected_positions = st.sidebar.multiselect("Position(s)", all_positions)
else:
    selected_positions = []

# --- Collapsible Stat Filters ---
categories = {
    "Pace": ["pace", "acceleration", "sprintspeed", "speed"],
    "Shooting": ["shooting", "finishing", "longshots", "volleys", "shotpower", "curve", "freekick", "headingaccuracy", "attackpositioning"],
    "Passing": ["passing", "shortpassing", "longpassing", "vision", "crossing"],
    "Dribbling / Skill": ["dribbling", "ballcontrol", "agility", "balance", "reactions", "skillmoves"],
    "Defending": ["defending", "markingawareness", "standingtackle", "slidingtackle", "interceptions", "aggression"],
    "Goalkeeping": ["diving", "handling", "kicking", "reflexes", "gkpositioning"],
    "Physical / Power": ["physic", "stamina", "strength", "jumping"],
    "Composure / Mentality": ["composure", "penalties"]
}

numeric_filters = {}
categorical_filters = {}

for cat, cols in categories.items():
    with st.sidebar.expander(cat, expanded=False):
        for col in cols:
            if col in df.columns and df[col].dtype in [int, float]:
                min_val = int(df[col].min())
                max_val = int(df[col].max())
                numeric_filters[col] = st.slider(
                    f"{col.replace('_', ' ').title()}",
                    min_val, max_val, (min_val, max_val)
                )

# Age filter
if "age" in df.columns:
    min_age = int(df["age"].min())
    max_age = int(df["age"].max())
    numeric_filters["age"] = st.sidebar.slider("Age", min_age, max_age, (min_age, max_age))

# Categorical filters
for col in ["skillmoves", "weakfoot", "preferredfoot"]:
    if col in df.columns:
        options = sorted(df[col].dropna().unique())
        categorical_filters[col] = st.sidebar.multiselect(col.title(), options)

# --- Apply Filters ---
filtered = df.copy()

# Numeric filters
for col, (min_val, max_val) in numeric_filters.items():
    filtered = filtered[(filtered[col] >= min_val) & (filtered[col] <= max_val)]

# Categorical filters
for col, selected in categorical_filters.items():
    if selected:
        filtered = filtered[filtered[col].isin(selected)]

# Position filter (fixed Salah logic)
if selected_positions:
    def has_position(player_positions):
        if pd.isna(player_positions):
            return False
        player_list = [pos.strip() for pos in player_positions.split(",")]
        return any(pos in player_list for pos in selected_positions)

    filtered = filtered[filtered["positions"].apply(has_position)]

# Format value + wage
if "value" in filtered.columns:
    filtered["value"] = filtered["value"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")
if "wage" in filtered.columns:
    filtered["wage"] = filtered["wage"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")

# --- Similar Player Finder ---
st.header("🔍 Find Similar Players")

top_n = st.slider("Number of top stats to compare", 3, 5, 3)
leeway = st.slider("Leeway for stat difference", 0, 20, 5)

target_player_name = st.selectbox("Select a player to find similar players:", df["shortname"].unique())
target_row = df[df["shortname"] == target_player_name].iloc[0]

non_stat_cols = [
    "shortname", "longname", "positions", "value", "wage", "age", "dob", "league", "club",
    "nationality", "preferredfoot", "weakfoot", "skillmoves", "releaseclause", "playertraits",
    "height", "heightft"
]

stat_cols = [
    col for col in df.columns
    if col not in non_stat_cols and pd.api.types.is_numeric_dtype(df[col])
]

df[stat_cols] = df[stat_cols].apply(pd.to_numeric, errors='coerce')

player_stats = target_row[stat_cols].dropna()
top_stats = player_stats.sort_values(ascending=False).head(top_n).index.tolist()

st.write("Comparing using these top stats:", top_stats)

target_positions = [p.strip() for p in str(target_row["positions"]).split(",")]

min_age_sim = df["age"].min()
max_age_sim = df["age"].max()
age_range_sim = st.slider("Filter by age", int(min_age_sim), int(max_age_sim), (int(min_age_sim), int(max_age_sim)))

def similarity_score(row):
    diff_sum = 0
    for stat in top_stats:
        if pd.isna(row[stat]) or pd.isna(target_row[stat]):
            return np.inf
        if abs(row[stat] - target_row[stat]) > leeway:
            return np.inf
        diff_sum += abs(row[stat] - target_row[stat])
    return diff_sum

df["similarity"] = df.apply(similarity_score, axis=1)

similar_players = df[(df["similarity"] != np.inf)]
similar_players = similar_players[similar_players["shortname"] != target_player_name]

similar_players = similar_players[
    similar_players["positions"].apply(lambda x: any(tp in x for tp in target_positions))
]

similar_players = similar_players[
    (similar_players["age"] >= age_range_sim[0]) &
    (similar_players["age"] <= age_range_sim[1])
]

similar_players = similar_players.sort_values("similarity", ascending=True)

similar_players["value"] = similar_players["value"].apply(lambda x: f"{int(x):,}")
similar_players["wage"] = similar_players["wage"].apply(lambda x: f"{int(x):,}")

st.subheader("Closest Matches")
st.dataframe(similar_players)

# --- Display Filtered Players ---
st.subheader(f"{len(filtered)} players found")
st.dataframe(filtered)

# --- Download button ---
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered players as CSV",
    data=csv,
    file_name="filtered_players.csv",
    mime="text/csv"
)
