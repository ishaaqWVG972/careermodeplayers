import streamlit as st
import pandas as pd

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
        "defenderpositioning", "vision", "penalties", "composure", "markingawareness", 
        "standingtackle", "slidingtackle", "diving", "handling", "kicking", 
        "gkpositioning", "reflexes", "speed"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filter Players")

# --- Position Filter ---
if "positions" in df.columns:
    # Gather all unique positions
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
    "Defending": ["defending", "markingawareness", "standingtackle", "slidingtackle", "interceptions", "defenderpositioning", "aggression"],
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
            if col in df.columns and df[col].dtype in [int, float]:
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

# Apply numeric filters
for col, (min_val, max_val) in numeric_filters.items():
    filtered = filtered[(filtered[col] >= min_val) & (filtered[col] <= max_val)]

# Apply categorical filters
for col, selected in categorical_filters.items():
    if selected:
        filtered = filtered[filtered[col].isin(selected)]

# Apply position filter
# --- Apply position filter ---
if selected_positions:
    def has_position(player_positions):
        if pd.isna(player_positions):
            return False
        # Split by comma, strip spaces, make list
        player_pos_list = [pos.strip() for pos in player_positions.split(",")]
        # Check if any selected position is in the player's positions
        return any(pos in player_pos_list for pos in selected_positions)

    filtered = filtered[filtered["positions"].apply(has_position)]

# --- Format value and wage for display ---
if "value" in filtered.columns:
    filtered["value"] = filtered["value"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")
if "wage" in filtered.columns:
    filtered["wage"] = filtered["wage"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")


# --- Display ---
st.subheader(f"{len(filtered)} players found")
st.dataframe(filtered)



# Download filtered results
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered players as CSV",
    data=csv,
    file_name="filtered_players.csv",
    mime="text/csv"
)
