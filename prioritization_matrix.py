import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
# Initialize SQLite database
conn = sqlite3.connect('initiatives.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS initiatives (
        id INTEGER PRIMARY KEY,
        name TEXT,
        impact INTEGER,
        feasibility INTEGER,
        work_stream TEXT,
        time_horizon TEXT
    )
''')
conn.commit()

# Function to load initiatives from the database
@st.cache_data
def load_initiatives():
    c.execute('SELECT * FROM initiatives')
    return c.fetchall()

# Function to add an initiative to the database
def add_initiative(name, impact, feasibility, work_stream, time_horizon):
    c.execute('INSERT INTO initiatives (name, impact, feasibility, work_stream, time_horizon) VALUES (?, ?, ?, ?, ?)',
              (name, impact, feasibility, work_stream, time_horizon))
    conn.commit()
    st.cache_data.clear()

# Function to remove an initiative from the database
def remove_initiative(initiative_id):
    c.execute('DELETE FROM initiatives WHERE id = ?', (initiative_id,))
    conn.commit()
    st.cache_data.clear()

# Function to update an initiative in the database
def update_initiative(initiative_id, name, impact, feasibility, work_stream, time_horizon):
    c.execute('''
        UPDATE initiatives
        SET name = ?, impact = ?, feasibility = ?, work_stream = ?, time_horizon = ?
        WHERE id = ?
    ''', (name, impact, feasibility, work_stream, time_horizon, initiative_id))
    conn.commit()
    st.cache_data.clear()

@st.dialog("Change your initiative information")
def edit_initiative(initiative_id, initiatives):
    df = pd.DataFrame(initiatives, columns=["ID", "Name", "Impact", "Feasibility", "Work Stream", "Time Horizon"])
    row = df[df['ID'] == initiative_id].iloc[0]

    with st.form(key=f"edit_form_{initiative_id}"):
        st.write("### Edit Initiative")
        new_name = st.text_input("Initiative Name", value=row['Name'])
        new_impact = st.slider("Impact Score (0-10)", 0, 10, row['Impact'])
        new_feasibility = st.slider("Feasibility Score (0-10)", 0, 10, row['Feasibility'])
        new_work_stream = st.selectbox("Work Stream", [row['Work Stream']], disabled=True)
        new_time_horizon = st.selectbox("Time Horizon", ["Long term", "Medium term", "Short term"], index=["Long term", "Medium term", "Short term"].index(row['Time Horizon']))
        submit_button = st.form_submit_button(label='Submit')
        
        if submit_button:
            update_initiative(initiative_id, new_name, new_impact, new_feasibility, new_work_stream, new_time_horizon)
            st.success(f"Initiative '{new_name}' updated.")
            st.rerun()

# Central view for adding and editing initiatives
def page_add_edit_initiative(selected_workstream):
    st.title("Add or Edit Initiative")

    # Add Initiative Form
    with st.form(key='add_initiative_form', clear_on_submit=True):
        st.write("### Add Initiative")
        initiative_name = st.text_input("Initiative Name")
        impact = st.slider("Impact Score (0-10)", 0, 10, 5)
        feasibility = st.slider("Feasibility Score (0-10)", 0, 10, 5)
        work_stream = st.selectbox("Work Stream", [selected_workstream], disabled=True)
        time_horizon = st.selectbox("Time Horizon", ["Long term", "Medium term", "Short term"])
        submit_button = st.form_submit_button(label='Submit')
        
        if submit_button:
            if initiative_name:
                add_initiative(initiative_name, impact, feasibility, work_stream, time_horizon)
                st.success(f"Initiative '{initiative_name}' added.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Please enter an initiative name.")

    # Edit Initiative Section
    st.divider()
    st.write("### Edit or Remove Initiative")
    initiatives = load_initiatives()
    if initiatives:
        df = pd.DataFrame(initiatives, columns=["ID", "Name", "Impact", "Feasibility", "Work Stream", "Time Horizon"])
        df = df[df["Work Stream"] == selected_workstream]

        for _, row in df.iterrows():
            st.divider()
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(row['ID'], " - ", row['Name'])
                with col2:
                    st.write(f'Impact: {row["Impact"]}')
                with col3:
                    st.write(f'Feasibility: {row["Feasibility"]}')

                col4 = st.columns([1])[0]
                with col4:
                    st.markdown(f"""
                        <div style="margin-top: 1rem; margin-bottom: 1rem; background-color: #f0f0f0; border-radius: 10px; padding: 10px; width: 100%;">
                            Description
                        </div>
                    """, unsafe_allow_html=True)

                col5, col6, col7, col8 = st.columns([2, 1, 1, 1])
                with col5:
                    st.markdown(f":blue-background[{row['Work Stream']}]")
                with col6:
                    st.markdown(f":blue-background[{row['Time Horizon']}]")
                with col7:
                    if st.button("Edit", key=f"edit_{row['ID']}", use_container_width=True):
                        edit_initiative(row['ID'], initiatives)
                with col8:
                    if st.button("Remove", key=f"remove_{row['ID']}", help="This action cannot be undone.", use_container_width=True):
                        remove_initiative(row['ID'])
                        st.error(f"Initiative '{row['Name']}' removed.")
                        st.rerun()

# Sidebar for navigation
st.sidebar.title("Navigation")
work_streams = ["Service Desk", "Deployment", "Reliability", "Finance", "Network"]
selected_workstream = st.sidebar.selectbox("Select Work Stream", work_streams)
page = st.sidebar.radio("Go to", ["Add/Edit Initiative", "Master View Initiatives"])



def page_master_view_initiatives():
    st.title("Master View Initiatives")

    time_horizon_filter = st.selectbox("Filter by Time Horizon", ["All", "Long term", "Medium term", "Short term"], index=0)
    work_stream_filter = st.selectbox("Filter by Work Stream", ["All"] + work_streams, index=0)

    initiatives = load_initiatives()
    if initiatives:
        df = pd.DataFrame(initiatives, columns=["ID", "Name", "Impact", "Feasibility", "Work Stream", "Time Horizon"])

        if time_horizon_filter != "All":
            df = df[df["Time Horizon"] == time_horizon_filter]

        if work_stream_filter != "All":
            df = df[df["Work Stream"] == work_stream_filter]

        # Create scatter plot using Altair with different shapes for time horizons
        st.write("### Prioritization Matrix")
        chart = alt.Chart(df).mark_point(size=200).encode(
            x=alt.X('Impact', scale=alt.Scale(domain=[0, 10])),
            y=alt.Y('Feasibility', scale=alt.Scale(domain=[0, 10])),
            color=alt.Color('Work Stream:N', scale=alt.Scale(scheme='category10')),
            shape=alt.Shape('Time Horizon:N', scale=alt.Scale(
                domain=['Short term', 'Medium term', 'Long term'],
                range=['circle', 'square', 'triangle-up']
            )),
            tooltip=['Name', 'Impact', 'Feasibility', 'Work Stream', 'Time Horizon']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

        st.dataframe(df, hide_index=True, height=500, use_container_width=True)

    # Auto-refresh every 20 seconds
    st_autorefresh(interval=20000, key="data_refresh")

# Page selection
if page == "Add/Edit Initiative":
    page_add_edit_initiative(selected_workstream)
elif page == "Master View Initiatives":
    page_master_view_initiatives()
