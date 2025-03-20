import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient

class Collaboration:
    def __init__(self):
        try:
            self.client = MongoClient(st.secrets['database']['link'])
            self.db = self.client['Collaborations']
            self.collection = self.db['collaborations']
        except Exception as e:
            st.error(f"Database connection error: {e}")

    def display(self):
        tab1, tab2 = st.tabs(["Sent", "Received"])
        with tab1:
            self.sent_tab()
        with tab2:
            self.received_tab()

    def sent_tab(self):
        col1, col2 = st.columns([1, 2], border=True)
        with col1:
            sender_email = st.text_input("Enter your email account")

        if sender_email:
            sent_data = list(self.collection.find({"sender": sender_email}))

            if sent_data:
                team_options = [f"Team {idx + 1}" for idx in range(len(sent_data))]
                selected_team = col1.radio("Your Teams", team_options)

                if selected_team:
                    team_index = int(selected_team.split()[1]) - 1
                    with col2:
                        team_info = sent_data[team_index]
                        st.subheader(f"Data for {selected_team}")
                        st.text(f"Team members : {team_info['team members']}")
                        for key, value in team_info.items():
                            if key.startswith("data_"):
                                st.subheader(value['key'],divider='blue')
                                st.text(value['description'])
                                st.dataframe(pd.DataFrame(value['data']))
            else:
                col1.warning("No data found for this email.")

    def received_tab(self):
        col1, col2 = st.columns([1, 2], border=True)
        with col1:
            sender_email = st.text_input("Enter sender's email")
            receiver_email = st.text_input("Enter your email")
            collaboration_date = st.date_input("Select collaboration date")

        if sender_email and receiver_email and collaboration_date:
            received_data = list(self.collection.find({
                "sender": sender_email,
                "team members": {"$in": [receiver_email]},
                "date": str(collaboration_date)
            }))

            if received_data:
                with col2:
                    st.subheader(f"Data received from {sender_email} on {collaboration_date}")
                    for data_entry in received_data:
                        for key, value in data_entry.items():
                            if key.startswith("data_"):
                                st.write(f"**{value['key']}**")
                                st.text(value['description'])
                                st.dataframe(pd.DataFrame(value['data']))
            else:
                col1.warning("No data found matching this combination.")
collab = Collaboration()
collab.display()
