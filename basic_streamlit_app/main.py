import streamlit as st
import pandas as pd

# Import dataset
players = "data/female_players.csv"
data_url = "https://raw.githubusercontent.com/kmgilland/GILLAND-Python-Portfolio/refs/heads/main/basic_streamlit_app/data/female_players.csv"
df = pd.read_csv(data_url, dtype=str)

# Introduction
st.title("EA Sports FC 25: Female Players Explorer")
st.write("Welcome, prospective managers! Here you can explore player ratings, stats, and filters for all female playable characters in EA Sports FC 25.")

# Position Mapping
position_map = {
    "GK": "Goalkeeper",
    "CB": "Center Back",
    "LB": "Left Back",
    "RB": "Right Back",
    "CDM": "Central Defensive Midfielder",
    "CM": "Central Midfielder",
    "CAM": "Central Attacking Midfielder",
    "LM": "Left Midfielder",
    "RM": "Right Midfielder",
    "LW": "Left Winger",
    "RW": "Right Winger",
    "ST": "Striker",
    "CF": "Center Forward"
}

df["Full Position"] = df["Position"].map(position_map).fillna(df["Position"])

# Sidebar filters
st.sidebar.header("Filter Players")

# Filter by Team
teams = sorted(df["Team"].dropna().unique())
selected_team = st.sidebar.selectbox("Select a Team:", ["All"] + teams)

# Filter by Nation
nations = sorted(df["Nation"].dropna().unique())
selected_nation = st.sidebar.selectbox("Select a Nation:", ["All"] + nations)

# Filter by Position
positions = sorted(df["Position"].dropna().unique())
selected_position = st.sidebar.selectbox("Select a Position:", ["All"] + positions)

# Filter by Overall Rating
ovr_min, ovr_max = int(df["OVR"].min()), int(df["OVR"].max())
ovr_range = st.sidebar.slider("Overall Rating Range:", ovr_min, ovr_max, (ovr_min, ovr_max))

# Apply Filters
filtered_df = df.copy()
if selected_team != "All":
    filtered_df = filtered_df[filtered_df["Team"] == selected_team]
if selected_nation != "All":
    filtered_df = filtered_df[filtered_df["Nation"] == selected_nation]
if selected_position != "All":
    filtered_df = filtered_df[filtered_df["Position"] == selected_position]
filtered_df = filtered_df[(filtered_df["OVR"] >= ovr_range[0]) & (filtered_df["OVR"] <= ovr_range[1])]

# Check if there are players after filtering
if filtered_df.empty:
    st.markdown(f"***There are no players that fit your selection.***")
else:
    # Show filtered DataFrame
    st.write(f"Showing {len(filtered_df)} players:")
    st.dataframe(filtered_df[["Name", "Position", "OVR", "PAC", "SHO", "PAS", "DRI", "DEF", "PHY", "Team", "Nation", "GK Diving", "GK Handling", "GK Kicking", "GK Positioning", "GK Reflexes"]])

    # Player Selection
    st.subheader("Player Details")
    selected_player = st.selectbox("Select a player to view details:", filtered_df["Name"].unique())
    player_info = filtered_df[filtered_df["Name"] == selected_player].iloc[0]

    # Display player stats
    st.write(f"### {player_info['Name']}")
    st.write(f"**Position:** {player_info['Full Position']}")
    st.write(f"**Overall Rating:** {player_info['OVR']}")

    if player_info['Position'] == 'GK':
        st.write(f"**GK Diving:** {int(player_info['GK Diving'])}, **GK Handling:** {int(player_info['GK Handling'])}, **GK Kicking:** {int(player_info['GK Kicking'])}")
        st.write(f"**GK Positioning:** {int(player_info['GK Positioning'])}, **GK Reflexes:** {int(player_info['GK Reflexes'])}")
        
        st.write(f"**Pace:** {player_info['PAC']}, **Shooting:** {player_info['SHO']}, **Passing:** {player_info['PAS']}")
        st.write(f"**Dribbling:** {player_info['DRI']}, **Defending:** {player_info['DEF']}, **Physicality:** {player_info['PHY']}")
    else:
        st.write(f"**Pace:** {player_info['PAC']}, **Shooting:** {player_info['SHO']}, **Passing:** {player_info['PAS']}")
        st.write(f"**Dribbling:** {player_info['DRI']}, **Defending:** {player_info['DEF']}, **Physicality:** {player_info['PHY']}")

    st.write(f"**Team:** {player_info['Team']}, **Nation:** {player_info['Nation']}")

    # Link to EA page
    if pd.notna(player_info['url']):
        st.markdown(f"[View Player on EA Sports Website]({player_info['url']})")
