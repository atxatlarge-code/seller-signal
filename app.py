import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Seller  Signal", layout="wide")

st.title("🏘️ Seller Signal")
st.markdown("""
Upload your **Main Properties** list and one or more **Distress Lists** (e.g., Code Violations, Tax Delinquency). 
The app will cross-reference addresses and assign a priority score (10 points per match).
""")

# --- Sidebar Settings ---
st.sidebar.header("Scoring Configuration")
points_per_match = st.sidebar.number_input("Points per list match", value=10, step=5)

# --- File Uploaders ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Main List")
    main_file = st.file_uploader("Upload properties.csv", type="csv")

with col2:
    st.subheader("2. Distress Lists")
    distress_files = st.file_uploader("Upload distress CSVs (Multiple allowed)", type="csv", accept_multiple_files=True)

# --- Processing ---
if main_file and distress_files:
    try:
        # Load main data
        df_main = pd.read_csv(main_file)
        
        # Check for address column
        if 'address' not in df_main.columns:
            st.error("Error: The main file must contain a column named 'address'.")
        else:
            # Prepare for matching
            df_main['score'] = 0
            # Create a normalized version for matching (lowercase and stripped)
            df_main['address_match_key'] = df_main['address'].astype(str).str.strip().str.lower()
            
            # Loop through each distress file
            for uploaded_file in distress_files:
                df_distress = pd.read_csv(uploaded_file)
                
                if 'address' in df_distress.columns:
                    # Get unique normalized addresses from the distress file
                    distress_keys = df_distress['address'].astype(str).str.strip().str.lower().unique()
                    
                    # Create a boolean mask for matches
                    mask = df_main['address_match_key'].isin(distress_keys)
                    
                    # Update score
                    df_main.loc[mask, 'score'] += points_per_match
                    
                    # Add a tracking column for this specific file
                    col_name = f"In: {uploaded_file.name}"
                    df_main[col_name] = mask
                else:
                    st.warning(f"Skipping '{uploaded_file.name}': No 'address' column found.")

            # --- Final Formatting ---
            # Remove the temporary matching key
            df_main = df_main.drop(columns=['address_match_key'])
            
            # Sort by highest score first
            df_main = df_main.sort_values(by='score', ascending=False)
            
            # MOVE SCORE TO FIRST COLUMN
            cols = ['score'] + [c for c in df_main.columns if c != 'score']
            df_main = df_main[cols]
            
            # --- Results Display ---
            st.divider()
            st.subheader("Processed Results")
            st.dataframe(df_main, use_container_width=True)
            
            # --- Download Button ---
            csv_data = df_main.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Scored Results (CSV)",
                data=csv_data,
                file_name="scored_properties_export.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")

else:
    st.info("Waiting for files... Please upload your main file and at least one distress list to begin.")

# --- Instructions ---
with st.expander("How to use this tool"):
    st.write("""
    1. **Format:** Ensure all files are `.csv` and contain a column exactly named `address`.
    2. **Logic:** If an address in your 'Main List' exists in a 'Distress List', it receives 10 points.
    3. **Scoring:** Points stack. A property in 3 distress lists will score 30.
    4. **Download:** Use the button above to save your prioritized lead list.
    """)
