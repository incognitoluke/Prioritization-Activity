import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
from streamlit_autorefresh import st_autorefresh


# Initialize SQLite database
conn = sqlite3.connect('initiatives.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS initiatives (
        id INTEGER PRIMARY KEY,
        name TEXT,
        impact INTEGER,
        feasibility INTEGER,
        work_stream TEXT
    )
''')
conn.commit()

# Function to load initiatives from the database
@st.cache_data
def load_initiatives():
    c.execute('SELECT * FROM initiatives')
    return c.fetchall()

# Function to add an initiative to the database
def add_initiative(name, impact, feasibility, work_stream):
    c.execute('INSERT INTO initiatives (name, impact, feasibility, work_stream) VALUES (?, ?, ?, ?)',
              (name, impact, feasibility, work_stream))
    conn.commit()
    st.cache_data.clear()

# Function to remove an initiative from the database
def remove_initiative(initiative_id):
    c.execute('DELETE FROM initiatives WHERE id = ?', (initiative_id,))
    conn.commit()

# Streamlit app
st.title("Prioritization Matrix")

# Input scores
impact = st.slider("Impact Score (0-10)", 0, 10, 5)
feasibility = st.slider("Feasibility Score (0-10)", 0, 10, 5)
initiative_name = st.text_input("Initiative Name")
work_stream = st.selectbox("Work Stream", ["Service Desk", "Deployment", "Reliability", "Finance", "Network"])

# Add initiative button
if st.button("Add Initiative"):
    if initiative_name:
        add_initiative(initiative_name, impact, feasibility, work_stream)
    else:
        st.warning("Please enter an initiative name.")

# Display initiatives
st.write("### Initiatives")
initiatives = load_initiatives()
if initiatives:
    df = pd.DataFrame(initiatives, columns=["ID", "Name", "Impact", "Feasibility", "Work Stream"])
    st.table(df)

    # Work stream filter
    work_stream_filter = st.selectbox("Filter by Work Stream", ["All"] + df["Work Stream"].unique().tolist())

    if work_stream_filter != "All":
        df = df[df["Work Stream"] == work_stream_filter]

    # Create scatter plot using Altair
    st.write("### Prioritization Matrix")
    chart = alt.Chart(df).mark_circle(size=200).encode(
        x=alt.X('Impact', scale=alt.Scale(domain=[0, 10])),
        y=alt.Y('Feasibility', scale=alt.Scale(domain=[0, 10])),
        color=alt.Color('Work Stream:N', scale=alt.Scale(scheme='category10')),
        tooltip=['Name', 'Impact', 'Feasibility', 'Work Stream']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

    # Remove initiative
    initiative_to_remove = st.selectbox("Select Initiative to Remove", df["Name"].tolist())
    if st.button("Remove Initiative"):
        initiative_id = df[df["Name"] == initiative_to_remove]["ID"].values[0]
        remove_initiative(initiative_id)
        st.success(f"Initiative '{initiative_to_remove}' removed.")

# Auto-refresh every 20 seconds
st_autorefresh(interval=2000, key="data_refresh")
