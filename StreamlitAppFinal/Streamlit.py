import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mticker

# --- Page Configuration ---
st.set_page_config( # Set up the page configuration 
    layout="wide",
    page_title="Blind Box Collector's Companion",
    page_icon="🎁"
)

# --- Constants ---

# URL for the master CSV data file on GitHub
DATA_URL = "https://raw.githubusercontent.com/kmgilland/GILLAND-Python-Portfolio/refs/heads/main/StreamlitAppFinal/box_data.csv"

EXPECTED_CSV_COLUMNS_FOR_APP_LOGIC = [
    'character_name',  # e.g., Peach Riot, Skullpanda
    'series_name',     # e.g., Rise Up, The Mare
    'figure_name',     # e.g., Poppy: Acorn, Birdy
    'price',
    'probability',
    'figure_photo',    # Optional
    'quantity'         # Optional, for pre-populating owned quantities
]

# APP_INTERNAL_COLUMNS defines the structure of the DataFrame stored in session state.
APP_INTERNAL_COLUMNS = [
    'character_series_name', # Data from CSV 'character_name'
    'series',                # Data from CSV 'series_name'
    'figure_name',           # Data from CSV 'figure_name'
    'price',                 # Data from CSV 'price'
    'probability',           # Data from CSV 'probability'
    'figure_photo'           # Data from CSV 'figure_photo'
]

# Expected columns for user's personal collection data (when uploading or manually adding)
USER_COLLECTION_COLUMNS = ['figure_name', 'series_name', 'sub_series_name', 'price_paid', 'owned_date', 'source', 'quantity']

# --- Helper Functions ---
def initialize_session_state():
    """Initializes session state variables if they don't exist."""
    if 'all_loaded_series_data_df' not in st.session_state: # Check if the DataFrame is already loaded
        st.session_state.all_loaded_series_data_df = pd.DataFrame(columns=APP_INTERNAL_COLUMNS)
    if 'figures_for_management_df' not in st.session_state: # DataFrame for figures to manage
        st.session_state.figures_for_management_df = pd.DataFrame(columns=APP_INTERNAL_COLUMNS)
    if 'user_collection_df' not in st.session_state: # DataFrame for user's collection
        # Ensure 'quantity' column is present and numeric from the start
        df = pd.DataFrame(columns=USER_COLLECTION_COLUMNS)
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        st.session_state.user_collection_df = df
    if 'target_figures' not in st.session_state: # List of target figures
        st.session_state.target_figures = []
    if 'selected_character_series_names' not in st.session_state: # List of selected character series names
        st.session_state.selected_character_series_names = []
    if 'selected_sub_series_map' not in st.session_state: # Map of selected sub-series for each character series
        st.session_state.selected_sub_series_map = {}
    if 'active_tab' not in st.session_state: # Active tab for navigation
        st.session_state.active_tab = "Manage My Collection"
    if 'data_load_attempted' not in st.session_state: # Flag to check if data load was attempted
        st.session_state.data_load_attempted = False

def convert_fraction_to_float(fraction_str):
    """Converts a fraction string (e.g., '1/12') to a float."""
    if isinstance(fraction_str, str) and '/' in fraction_str: # Check if it's a fraction
        try:
            num, den = fraction_str.split('/') # Split into numerator and denominator
            return float(num) / float(den) # Convert to float
        except ValueError: # Handle invalid fractions
            return np.nan
    elif pd.isna(fraction_str): # Handle NaN values
        return np.nan
    else: # Handle non-fraction strings
        try:
            return float(fraction_str) # Convert to float if it's not a fraction
        except ValueError: # Handle invalid float conversion
            return np.nan

# --- UI Helper for Dynamic Sub-Series Selection ---
def display_sub_series_selectors():
    """Displays multiselect widgets for sub-series based on selected character series."""
    if not isinstance(st.session_state.all_loaded_series_data_df, pd.DataFrame) or st.session_state.all_loaded_series_data_df.empty: # Check if DataFrame is valid
        st.sidebar.warning("Master data not loaded or empty. Sub-series selection unavailable.")
        return

    for char_series_name_internal in st.session_state.selected_character_series_names: # Iterate over selected character series
        sub_series_in_char_series = sorted(st.session_state.all_loaded_series_data_df[
            st.session_state.all_loaded_series_data_df['character_series_name'] == char_series_name_internal
        ]['series'].unique()) # Get unique sub-series for the character series

        if sub_series_in_char_series: # Check if there are sub-series available
            with st.sidebar.expander(f"Sub-Series for {char_series_name_internal}", expanded=True): # Create an expander for each character series
                current_selections = st.session_state.selected_sub_series_map.get(char_series_name_internal, []) # Get current selections from session state
                valid_current_selections = [sel for sel in current_selections if sel in sub_series_in_char_series] # Validate current selections

                selected_subs = st.multiselect( # Multiselect for sub-series
                    f"Select Sub-Series from {char_series_name_internal}:", # Label
                    options=sub_series_in_char_series, # Options
                    default=valid_current_selections, # Default selections
                    key=f"sub_series_multiselect_{char_series_name_internal.replace(' ', '_')}" # Unique key for each multiselect
                )
                st.session_state.selected_sub_series_map[char_series_name_internal] = selected_subs # Update session state with selected sub-series

# --- Main Application Logic ---
def main():
    """Main function to run the Streamlit application."""
    initialize_session_state()

    st.title("🎁 Blind Box Collector's Companion")
    st.markdown("Manage your blind box collection, track your targets, and analyze your chances!")

    # --- Auto Load Master Collection Data ---
    if not st.session_state.data_load_attempted or \
       ('all_loaded_series_data_df' in st.session_state and st.session_state.all_loaded_series_data_df.empty and not st.session_state.data_load_attempted): # Check if data load was attempted
        st.session_state.data_load_attempted = True # Set the flag to indicate data load was attempted
        try: # Attempt to load the CSV file
            df = pd.read_csv(DATA_URL, dtype=str) # Load the CSV file into a DataFrame

            csv_cols_needed_for_core_functionality = ['character_name', 'series_name', 'figure_name', 'price', 'probability']
            missing_cols = [col for col in csv_cols_needed_for_core_functionality if col not in df.columns] # Check for missing columns

            if missing_cols:
                st.error(f"Critical Error: The CSV data from the URL is missing the following essential columns: {', '.join(missing_cols)}. "
                         "The application cannot proceed without them. Please check the CSV file at the source.") # Error message for missing columns
                st.session_state.all_loaded_series_data_df = pd.DataFrame(columns=APP_INTERNAL_COLUMNS) # Initialize empty DataFrame
            else: # Process the DataFrame
                df.rename(columns={
                    'character_name': 'character_series_name',
                    'series_name': 'series'
                }, inplace=True)

                if 'price' in df.columns: # Convert price to numeric
                    df['price'] = df['price'].astype(str).str.replace('$', '', regex=False)
                    df['price'] = pd.to_numeric(df['price'], errors='coerce')

                if 'probability' in df.columns: # Convert probability to numeric
                    df['probability'] = df['probability'].apply(convert_fraction_to_float)
                    df['probability'] = pd.to_numeric(df['probability'], errors='coerce')

                if 'figure_photo' not in df.columns: # Check if figure_photo column exists
                    df['figure_photo'] = pd.NA # Initialize with NA if not present
                else:
                    df['figure_photo'] = df['figure_photo'].astype(str).replace('', pd.NA) # Convert empty strings to NA
                
                # Quantity from master CSV is not currently used by APP_INTERNAL_COLUMNS,
                # but might be used if pre-populating user_collection_df.

                essential_cols_for_dropna = ['character_series_name', 'series', 'figure_name', 'price', 'probability']
                for col_name in ['character_series_name', 'series', 'figure_name']:
                    if col_name in df.columns: # Check if column exists
                        df[col_name] = df[col_name].astype(str) # Convert to string to avoid NaN issues

                df.dropna(subset=essential_cols_for_dropna, inplace=True) # Drop rows with NaN in essential columns
                
                for col_internal in APP_INTERNAL_COLUMNS: # Check if internal columns exist in the DataFrame
                    if col_internal not in df.columns:
                        df[col_internal] = pd.NA # Should mainly apply to figure_photo

                st.session_state.all_loaded_series_data_df = df[APP_INTERNAL_COLUMNS].drop_duplicates().reset_index(drop=True) # Remove duplicates and reset index

                if st.session_state.all_loaded_series_data_df.empty: # Check if DataFrame is empty after processing
                    st.warning("Warning: No valid data rows found in 'box_data.csv' after processing. ")
                else:
                    st.success(f"Successfully auto-loaded and processed data from 'box_data.csv'. "
                               f"{len(st.session_state.all_loaded_series_data_df)} unique figures loaded.")
                    st.session_state.selected_character_series_names = []
                    st.session_state.selected_sub_series_map = {}
                    st.session_state.figures_for_management_df = pd.DataFrame(columns=APP_INTERNAL_COLUMNS)

        except FileNotFoundError:
            st.error(f"Critical Error: The data file 'box_data.csv' was not found. ")
            st.session_state.all_loaded_series_data_df = pd.DataFrame(columns=APP_INTERNAL_COLUMNS)
        except pd.errors.EmptyDataError:
            st.error("Critical Error: The CSV file 'box_data.csv' is empty.")
            st.session_state.all_loaded_series_data_df = pd.DataFrame(columns=APP_INTERNAL_COLUMNS)
        except Exception as e:
            st.error(f"An unexpected error occurred while auto-loading or processing 'box_data.csv': {e}. ")
            st.session_state.all_loaded_series_data_df = pd.DataFrame(columns=APP_INTERNAL_COLUMNS)

    with st.sidebar: # Sidebar for filtering and managing figures
        st.header("⚙️ Collection Setup")
        st.subheader("Filter Figures for Management")
        if not st.session_state.all_loaded_series_data_df.empty: # Check if DataFrame is not empty
            available_char_series_for_selection = sorted(st.session_state.all_loaded_series_data_df['character_series_name'].unique())
            st.session_state.selected_character_series_names = st.multiselect(
                "Select Character Series to Manage:",
                options=available_char_series_for_selection,
                default=st.session_state.selected_character_series_names,
                key="character_series_selector_main"
            )
            display_sub_series_selectors() #
            if st.button("Show Figures from Selected Sub-Series", key="filter_figures_button"): # Button to filter figures
                if not st.session_state.selected_character_series_names: # Check if any character series is selected
                    st.warning("Please select at least one character series.")
                else:
                    filtered_dfs = []
                    for char_series_name_internal, sub_series_list in st.session_state.selected_sub_series_map.items(): # Iterate over selected character series and their sub-series
                        if char_series_name_internal in st.session_state.selected_character_series_names and sub_series_list: # Check if character series is selected and sub-series list is not empty
                            series_data = st.session_state.all_loaded_series_data_df[
                                (st.session_state.all_loaded_series_data_df['character_series_name'] == char_series_name_internal) &
                                (st.session_state.all_loaded_series_data_df['series'].isin(sub_series_list))
                            ]
                            if not series_data.empty:
                                filtered_dfs.append(series_data)
                    if filtered_dfs: # Check if any filtered DataFrames are available
                        st.session_state.figures_for_management_df = pd.concat(filtered_dfs, ignore_index=True).drop_duplicates()
                        st.success(f"Displaying {len(st.session_state.figures_for_management_df)} figures. Go to 'Manage My Collection' tab.")
                        st.session_state.active_tab = "Manage My Collection"
                    else:
                        st.warning("No figures found for the selected character series / sub-series combination.")
                        st.session_state.figures_for_management_df = pd.DataFrame(columns=APP_INTERNAL_COLUMNS)
        else:
            st.info("Master data is not loaded or is empty. Filtering options are unavailable.")

        st.subheader("Set Target Figures") # Sidebar for setting target figures
        if not st.session_state.figures_for_management_df.empty:
            all_manageable_figures = sorted(st.session_state.figures_for_management_df['figure_name'].unique().tolist())
            st.session_state.target_figures = st.multiselect(
                "Select Your Target Figures (from shown sub-series):",
                options=all_manageable_figures,
                default=st.session_state.target_figures,
                help="Choose figures you are aiming to collect."
            )
        elif st.session_state.all_loaded_series_data_df.empty:
             st.info("Master data is not loaded. Target selection unavailable.")
        else:
            st.info("Filter and show figures first to enable target selection.")

        st.subheader("Add/Edit Other Owned Figures") # Sidebar for adding/editing owned figures
        collection_input_method = st.radio(
            "Input method for other figures or to edit details:",
            ("Enter Manually", "Upload CSV"),
            key="collection_input_method_sidebar"
        )
        if collection_input_method == "Enter Manually": # Manual entry form
            with st.form("manual_add_figure_form_sidebar", clear_on_submit=True):
                st.markdown("Add/Update a figure in your collection:")
                figure_name_manual = st.text_input("Figure Name*")
                char_series_name_manual_input = st.text_input("Character Series Name (e.g., Peach Riot)*") 
                sub_series_name_manual_input = st.text_input("Sub-Series Name (e.g., Rise Up)*") 
                price_paid_manual = st.number_input("Price Paid*", min_value=0.0, step=0.01, format="%.2f")
                quantity_manual = st.number_input("Quantity*", min_value=1, value=1, step=1) # New quantity input
                owned_date_manual = st.date_input("Date Acquired (Optional)", value=None)
                source_manual = st.selectbox("Source", ["Marked Owned", "Manual Entry", "CSV Upload"], index=1)
                submitted_manual = st.form_submit_button("Add/Update Figure")

                if submitted_manual and figure_name_manual and char_series_name_manual_input and sub_series_name_manual_input and price_paid_manual is not None and quantity_manual > 0:
                    existing_entry_index = st.session_state.user_collection_df[
                        st.session_state.user_collection_df['figure_name'] == figure_name_manual
                    ].index

                    entry_data = {
                        'figure_name': figure_name_manual, 
                        'series_name': char_series_name_manual_input,
                        'sub_series_name': sub_series_name_manual_input,
                        'price_paid': price_paid_manual,
                        'owned_date': pd.to_datetime(owned_date_manual) if owned_date_manual else pd.NaT,
                        'source': source_manual,
                        'quantity': quantity_manual # Add quantity
                    }
                    if not existing_entry_index.empty: # Check if entry already exists
                        idx_to_update = existing_entry_index[0]
                        for col, val in entry_data.items():
                            st.session_state.user_collection_df.loc[idx_to_update, col] = val
                        st.success(f"Updated '{figure_name_manual}'.")
                    else: 
                        new_entry_df = pd.DataFrame([entry_data], columns=USER_COLLECTION_COLUMNS)
                        st.session_state.user_collection_df = pd.concat(
                            [st.session_state.user_collection_df, new_entry_df], ignore_index=True
                        ) # Concatenate new entry
                        st.session_state.user_collection_df = st.session_state.user_collection_df.drop_duplicates(subset=['figure_name'], keep='last').reset_index(drop=True)
                        st.success(f"Added '{figure_name_manual}'.")
                elif submitted_manual:
                    st.warning("Please fill in all required fields and ensure quantity is at least 1.")

        elif collection_input_method == "Upload CSV": # CSV upload form
            uploaded_collection_file = st.file_uploader(
                "Upload Your Collection CSV:", 
                type=['csv'], 
                help=f"Expected CSV columns: {', '.join(USER_COLLECTION_COLUMNS)}. 'quantity' is optional (defaults to 1)."
            )
            if uploaded_collection_file: # Check if a file is uploaded
                try:
                    df_user_upload = pd.read_csv(uploaded_collection_file)
                    required_upload_cols = ['figure_name', 'series_name', 'sub_series_name', 'price_paid'] # quantity is optional
                    missing_upload_cols = [col for col in required_upload_cols if col not in df_user_upload.columns]

                    if not missing_upload_cols: # Check if required columns are present
                        for col_uc in USER_COLLECTION_COLUMNS: 
                            if col_uc not in df_user_upload.columns:
                                if col_uc == 'quantity':
                                    df_user_upload[col_uc] = 1 # Default quantity to 1 if not in CSV
                                else:
                                    df_user_upload[col_uc] = pd.NA 
                        
                        df_user_upload['price_paid'] = pd.to_numeric(df_user_upload['price_paid'], errors='coerce')
                        df_user_upload['owned_date'] = pd.to_datetime(df_user_upload['owned_date'], errors='coerce')
                        df_user_upload['quantity'] = pd.to_numeric(df_user_upload['quantity'], errors='coerce').fillna(1).astype(int)
                        df_user_upload['source'] = df_user_upload['source'].fillna("CSV Upload")
                        
                        # Consolidate with existing collection, updating quantities for matching figure_names
                        for index, row_upload in df_user_upload.iterrows():
                            existing_entry = st.session_state.user_collection_df[
                                st.session_state.user_collection_df['figure_name'] == row_upload['figure_name']
                            ]
                            if not existing_entry.empty:
                                existing_idx = existing_entry.index[0]
                                # Update existing entry, especially quantity and price if source is also CSV
                                st.session_state.user_collection_df.loc[existing_idx, 'quantity'] = row_upload['quantity']
                                st.session_state.user_collection_df.loc[existing_idx, 'price_paid'] = row_upload['price_paid']
                                st.session_state.user_collection_df.loc[existing_idx, 'series_name'] = row_upload['series_name']
                                st.session_state.user_collection_df.loc[existing_idx, 'sub_series_name'] = row_upload['sub_series_name']
                                st.session_state.user_collection_df.loc[existing_idx, 'owned_date'] = row_upload['owned_date']
                                st.session_state.user_collection_df.loc[existing_idx, 'source'] = row_upload['source']

                            else:
                                st.session_state.user_collection_df = pd.concat(
                                    [st.session_state.user_collection_df, pd.DataFrame([row_upload], columns=USER_COLLECTION_COLUMNS)],
                                    ignore_index=True
                                )
                        st.session_state.user_collection_df = st.session_state.user_collection_df.drop_duplicates(subset=['figure_name'], keep='last').reset_index(drop=True)
                        st.success("Collection CSV processed and merged/updated.")
                    else: 
                        st.error(f"Uploaded CSV is missing required columns: {', '.join(missing_upload_cols)}. ")
                except Exception as e: st.error(f"Error processing collection CSV: {e}")

    tab_list = ["Manage My Collection", "🎯 Target Overview", "📊 My Collection Stats", "🎲 Probability Workbench", "📚 Browse Loaded Series"]
    try:
        default_tab_index = tab_list.index(st.session_state.active_tab)
    except ValueError: default_tab_index = 0 

    manage_tab, target_tab, stats_tab, prob_tab, browse_tab = st.tabs(tab_list)

    with manage_tab: # Main tab for managing collection
        st.header("Manage My Collection (Figures from Selected Sub-Series)")
        if st.session_state.all_loaded_series_data_df.empty:
            st.info("Master data ('box_data.csv') could not be loaded or is empty.")
        elif st.session_state.figures_for_management_df.empty:
            st.info("No figures loaded for management. Use 'Filter Figures' in the sidebar.")
        else:
            st.markdown(f"Mark figures you own from the **{len(st.session_state.figures_for_management_df)}** figures shown.")
            

            for index, fig_to_manage_row in st.session_state.figures_for_management_df.iterrows(): # Iterate over each figure
                fig_name = fig_to_manage_row['figure_name']
                fig_char_series = fig_to_manage_row['character_series_name']
                fig_sub_series = fig_to_manage_row['series']
                fig_box_price = fig_to_manage_row['price']
                fig_photo_url = fig_to_manage_row['figure_photo']

                unique_key_base = f"{fig_char_series.replace(' ','_')}_{fig_sub_series.replace(' ','_')}_{fig_name.replace(' ','_')}" # Unique key for each figure
                
                owned_entry = st.session_state.user_collection_df[
                    st.session_state.user_collection_df['figure_name'] == fig_name
                ] # Check if figure is already owned
                
                is_owned_in_df = not owned_entry.empty and owned_entry['quantity'].iloc[0] > 0
                current_qty_in_df = owned_entry['quantity'].iloc[0] if not owned_entry.empty else 0

                cols = st.columns([0.5, 2, 1, 1]) # Create columns for layout
                with cols[0]: # Column for checkbox
                    checkbox_state = st.checkbox("Own", value=is_owned_in_df, key=f"owned_cb_{unique_key_base}")
                
                with cols[1]: # Column for figure details
                    st.subheader(f"{fig_name}")
                    st.caption(f"Character: {fig_char_series} | Sub-Series: {fig_sub_series} | Box Price: ${fig_box_price:.2f}")

                with cols[2]: # Column for quantity input
                    if checkbox_state:
                        default_slider_qty = current_qty_in_df if current_qty_in_df > 0 else 1
                        quantity_input = st.number_input(
                            "Quantity", 
                            min_value=1, 
                            value=default_slider_qty, 
                            step=1, 
                            key=f"qty_ni_{unique_key_base}",
                            label_visibility="collapsed" # More compact
                        )
                    else:
                        # Placeholder to maintain layout if not checked
                        st.empty() 
                
                with cols[3]:
                    if pd.notna(fig_photo_url) and isinstance(fig_photo_url, str) and (fig_photo_url.startswith('http') or '.jpg' in fig_photo_url or '.png' in fig_photo_url) : # Basic check for image
                        # If figure_photo_url are just filenames like "image.jpg", they must be in the same dir as Streamlit.py
                        st.image(fig_photo_url, width=75, caption="Figure")
                    else:
                        st.caption("No image")
                st.divider()

                # --- Logic to update user_collection_df based on interactions ---
                existing_entry_idx = owned_entry.index[0] if not owned_entry.empty else None

                if checkbox_state: # If checkbox is checked
                    new_quantity = quantity_input # Get value from the number input
                    if existing_entry_idx is not None: # Figure exists in user collection
                        st.session_state.user_collection_df.loc[existing_entry_idx, 'quantity'] = new_quantity
                        # If it was marked owned, update price to current box price, and series info
                        if st.session_state.user_collection_df.loc[existing_entry_idx, 'source'] == 'Marked Owned' or pd.isna(st.session_state.user_collection_df.loc[existing_entry_idx, 'source']):
                            st.session_state.user_collection_df.loc[existing_entry_idx, 'price_paid'] = fig_box_price
                            st.session_state.user_collection_df.loc[existing_entry_idx, 'series_name'] = fig_char_series
                            st.session_state.user_collection_df.loc[existing_entry_idx, 'sub_series_name'] = fig_sub_series
                    else: # Figure does not exist, add new entry
                        new_data = {
                            'figure_name': fig_name,
                            'series_name': fig_char_series,
                            'sub_series_name': fig_sub_series,
                            'price_paid': fig_box_price,
                            'owned_date': pd.NaT,
                            'source': 'Marked Owned',
                            'quantity': new_quantity
                        }
                        new_df_row = pd.DataFrame([new_data], columns=USER_COLLECTION_COLUMNS)
                        st.session_state.user_collection_df = pd.concat(
                            [st.session_state.user_collection_df, new_df_row],
                            ignore_index=True
                        )
                        # Ensure one entry per figure_name after adding, taking the latest (this one)
                        st.session_state.user_collection_df = st.session_state.user_collection_df.drop_duplicates(subset=['figure_name'], keep='last').reset_index(drop=True)

                else: # If checkbox is NOT checked
                    if existing_entry_idx is not None:
                        # Set quantity to 0. The entry remains but won't be counted as "owned" in stats.
                        st.session_state.user_collection_df.loc[existing_entry_idx, 'quantity'] = 0
            
            if st.button("Refresh Collection View & Stats", key="refresh_collection_button_main"):
                st.rerun()
            
            st.subheader("Current Personal Collection Summary (Owned: Qty > 0, Last 5)")
            display_owned_collection = st.session_state.user_collection_df[st.session_state.user_collection_df['quantity'] > 0]
            if not display_owned_collection.empty:
                st.dataframe(display_owned_collection.tail(), use_container_width=True) 
                st.caption(f"Total unique figure types with quantity > 0: {len(display_owned_collection)}")
            else:
                st.caption("Your personal collection (with quantity > 0) is currently empty.")

    with target_tab:
        st.header("🎯 Target Figure Overview")
        if st.session_state.all_loaded_series_data_df.empty:
            st.info("Master data ('box_data.csv') could not be loaded or is empty.")
        elif not st.session_state.target_figures:
            st.info("No target figures selected. Use 'Set Target Figures' in the sidebar.")
        else:
            targets_details_df = st.session_state.all_loaded_series_data_df[
                st.session_state.all_loaded_series_data_df['figure_name'].isin(st.session_state.target_figures)
            ].drop_duplicates(subset=['figure_name', 'character_series_name', 'series']).copy()

            if targets_details_df.empty and st.session_state.target_figures:
                 st.warning("Selected target figures are not found in the loaded master data.")
            else:
                st.markdown(f"You have selected **{len(st.session_state.target_figures)}** target figure(s).")
                for index, row in targets_details_df.iterrows():
                    st.subheader(row['figure_name'])
                    owned_info = st.session_state.user_collection_df[
                        (st.session_state.user_collection_df['figure_name'] == row['figure_name']) &
                        (st.session_state.user_collection_df['quantity'] > 0)
                    ]
                    status_text = "❌ Not Owned"
                    price_paid_text = ""
                    quantity_owned_text = ""

                    if not owned_info.empty:
                        status_text = f"✅ Owned"
                        qty = owned_info['quantity'].iloc[0]
                        if qty > 0 : quantity_owned_text = f" (Quantity: {qty})" # Display quantity
                        
                        price_paid_val = owned_info['price_paid'].iloc[0]
                        if pd.notna(price_paid_val):
                            price_paid_text = f"**You Paid (per unit):** ${float(price_paid_val):.2f}"


                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if pd.notna(row['figure_photo']) and isinstance(row['figure_photo'], str) and (row['figure_photo'].startswith('http') or '.jpg' in row['figure_photo'] or '.png' in row['figure_photo']):
                            st.image(row['figure_photo'], width=100, caption="Target Figure")
                        else: st.caption("No image URL")
                    with col2:
                        st.markdown(f"**Character:** {row['character_series_name']} | **Sub-Series:** {row['series']}")
                        st.markdown(f"**Box Price:** ${row['price']:.2f} | **Pull Probability:** {row['probability']:.2%}")
                        st.markdown(f"**Status:** {status_text}{quantity_owned_text}")
                        if price_paid_text:
                             st.markdown(price_paid_text)
                    st.divider()

    with stats_tab:
        st.header("📊 My Collection Statistics")
        # Filter for items with quantity > 0 for display and calculations
        active_collection_df = st.session_state.user_collection_df[st.session_state.user_collection_df['quantity'] > 0].copy()

        if active_collection_df.empty:
            st.info("No figures with quantity > 0 in your collection yet.")
        else:
            st.subheader("My Full Collection List (Owned Figures):")
            st.dataframe(active_collection_df[USER_COLLECTION_COLUMNS], use_container_width=True)

            # Calculate total spent considering quantity
            active_collection_df['total_value_for_figure'] = pd.to_numeric(active_collection_df['price_paid'], errors='coerce') * pd.to_numeric(active_collection_df['quantity'], errors='coerce')
            total_spent = active_collection_df['total_value_for_figure'].sum()
            
            total_individual_figures = active_collection_df['quantity'].sum() # Sum of quantities
            
            avg_cost_per_individual_figure = total_spent / total_individual_figures if total_individual_figures > 0 else 0

            st.subheader("Summary:")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Individual Figures Owned", f"{total_individual_figures}") # Changed metric
            col2.metric("Total Amount Spent", f"${total_spent:.2f}")
            col3.metric("Avg. Cost Per Individual Figure", f"${avg_cost_per_individual_figure:.2f}") # Changed metric

            if total_individual_figures > 0 and 'price_paid' in active_collection_df.columns:
                valid_prices_paid_per_unit = pd.to_numeric(active_collection_df['price_paid'], errors='coerce').dropna()
                
                if not valid_prices_paid_per_unit.empty:
                    st.subheader("Distribution of Prices Paid (Per Unit)")
                    fig, ax = plt.subplots()
                    # Create a list of prices, repeated by quantity for a more representative histogram of individual purchases
                    prices_for_hist = []
                    for _, row_hist in active_collection_df.iterrows():
                        if pd.notna(row_hist['price_paid']) and pd.notna(row_hist['quantity']):
                             prices_for_hist.extend([float(row_hist['price_paid'])] * int(row_hist['quantity']))
                    
                    if prices_for_hist:
                        sns.histplot(prices_for_hist, kde=True, ax=ax, bins=max(1, min(20, int(len(prices_for_hist)/2))))
                        ax.set_title("Histogram of Prices Paid (Per Unit, Reflecting Quantities)")
                        ax.set_xlabel("Price Paid ($)")
                        ax.set_ylabel("Number of Individual Figures")
                        st.pyplot(fig)
                        plt.close(fig)
                    else:
                        st.caption("Not enough data for price distribution histogram.")

                else:
                    st.caption("No valid price data to plot histogram.")

    with prob_tab:
        st.header("🎲 Probability Workbench")
        if st.session_state.all_loaded_series_data_df.empty:
            st.info("Master data ('box_data.csv') could not be loaded or is empty.")
        elif not st.session_state.target_figures:
            st.info("Select target figures from 'Set Target Figures' in the sidebar.")
        else:
            # Get figures that are targets AND have quantity 0 or are not in user_collection_df
            unowned_target_names = []
            for target_name in st.session_state.target_figures:
                owned_entry = st.session_state.user_collection_df[st.session_state.user_collection_df['figure_name'] == target_name]
                if owned_entry.empty or owned_entry['quantity'].iloc[0] == 0:
                    unowned_target_names.append(target_name)

            if not unowned_target_names:
                st.success("🎉 Congratulations! You own all your selected target figures (with quantity > 0).")
            else:
                st.subheader("Analyze Chances for Unowned Targets")
                st.markdown(f"Targeting **{len(unowned_target_names)}** unowned figure(s): _{', '.join(unowned_target_names)}_")

                unowned_targets_details_df = st.session_state.all_loaded_series_data_df[
                    st.session_state.all_loaded_series_data_df['figure_name'].isin(unowned_target_names)
                ].drop_duplicates(subset=['figure_name', 'character_series_name', 'series'])

                if unowned_targets_details_df.empty:
                    st.warning("Could not find details for unowned targets in loaded master data.")
                else:
                    available_sub_series_for_prob = [""] + sorted(unowned_targets_details_df['series'].unique().tolist()) 
                    if len(available_sub_series_for_prob) <=1:
                        st.warning("No sub-series associated with your unowned targets found in loaded data.")
                    else:
                        selected_sub_series_to_buy = st.selectbox(
                            "Select a Sub-Series (containing one of your targets) to 'Buy' From:",
                            options=available_sub_series_for_prob, index=0, key="prob_sub_series_select"
                        )
                        if selected_sub_series_to_buy: 
                            targets_in_selected_sub_series_df = unowned_targets_details_df[
                                unowned_targets_details_df['series'] == selected_sub_series_to_buy
                            ]
                            if targets_in_selected_sub_series_df.empty: 
                                st.warning(f"No unowned targets found in '{selected_sub_series_to_buy}'.")
                            else:
                                prob_of_any_specific_target_in_sub_series = targets_in_selected_sub_series_df['probability'].sum()
                                if 'price' not in targets_in_selected_sub_series_df.columns or targets_in_selected_sub_series_df['price'].empty or pd.isna(targets_in_selected_sub_series_df['price'].iloc[0]):
                                    st.error(f"Price information missing or invalid for sub-series '{selected_sub_series_to_buy}'.")
                                else:
                                    box_price = targets_in_selected_sub_series_df['price'].iloc[0] 
                                    st.metric(f"Std. Box Price for '{selected_sub_series_to_buy}'", f"${box_price:.2f}")
                                    st.markdown(f"Combined probability of pulling *any* of these targets "
                                                f"({', '.join(targets_in_selected_sub_series_df['figure_name'])}) "
                                                f"from one box of '{selected_sub_series_to_buy}' is: "
                                                f"**{prob_of_any_specific_target_in_sub_series:.2%}**")
                                    num_boxes = st.slider("Number of Boxes to Simulate:", 1, 100, 10, key=f"slider_prob_{selected_sub_series_to_buy.replace(' ','_')}")
                                    prob_no_target_one_box = 1 - prob_of_any_specific_target_in_sub_series
                                    if prob_no_target_one_box < 0: prob_no_target_one_box = 0
                                    prob_at_least_one_N_boxes = 1 - (prob_no_target_one_box ** num_boxes)
                                    st.metric(f"P(At Least One Target) in {num_boxes} boxes:", f"{prob_at_least_one_N_boxes:.2%}")
                                    st.markdown(f"Simulated cost for {num_boxes} boxes: **${num_boxes * box_price:.2f}**")
                                    box_counts = np.arange(1, 51)
                                    probs = [1 - (prob_no_target_one_box ** count) for count in box_counts]
                                    fig_prob, ax_prob = plt.subplots()
                                    sns.lineplot(x=box_counts, y=probs, ax=ax_prob, marker='o')
                                    ax_prob.set_title(f"Chance of Target from '{selected_sub_series_to_buy}'")
                                    ax_prob.set_xlabel("Number of Boxes")
                                    ax_prob.set_ylabel("P(At Least One Target)")
                                    ax_prob.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
                                    ax_prob.grid(True, linestyle='--', alpha=0.7)
                                    st.pyplot(fig_prob)
                                    plt.close(fig_prob)
                        else:
                            st.info("Select a sub-series to see probability calculations.")

    with browse_tab:
        st.header("📚 Browse All Figures from Loaded Master Data")
        if st.session_state.all_loaded_series_data_df.empty:
            st.info("Master data ('box_data.csv') could not be loaded or is empty.")
        else:
            st.markdown(f"Displaying all {len(st.session_state.all_loaded_series_data_df)} figures from 'box_data.csv'.")
            display_df_browse = st.session_state.all_loaded_series_data_df.copy()
            char_series_filter_options = ["All Character Series"] + sorted(display_df_browse['character_series_name'].unique().tolist())
            selected_char_series_filter = st.selectbox("Filter by Character Series:", char_series_filter_options, key="browse_char_series_filter")
            if selected_char_series_filter != "All Character Series":
                display_df_browse = display_df_browse[display_df_browse['character_series_name'] == selected_char_series_filter]
            if not display_df_browse.empty and selected_char_series_filter != "All Character Series":
                sub_series_filter_options = ["All Sub-Series"] + sorted(display_df_browse['series'].unique().tolist())
                selected_sub_series_filter = st.selectbox(f"Filter by Sub-Series within {selected_char_series_filter}:", sub_series_filter_options, key="browse_sub_series_filter")
                if selected_sub_series_filter != "All Sub-Series":
                    display_df_browse = display_df_browse[display_df_browse['series'] == selected_sub_series_filter]
            st.dataframe(
                display_df_browse[['figure_name', 'character_series_name', 'series', 'price', 'probability']], 
                use_container_width=True
            )

    st.markdown("---")
    st.markdown("Built with ❤️ by a fellow collector, powered by Streamlit.")

if __name__ == "__main__":
    main()
