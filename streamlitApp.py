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

                        for key, value in team_info.items():
                            if key.startswith("data_"):
                                st.subheader(value['key'],divider='blue')
                                st.text(value['description'])
                                st.dataframe(pd.DataFrame(value['data']))
                         # Display Comments
                        st.markdown("### Comments")
                        comments = team_info.get("comments", {})
                        if comments:
                            for member, comments_list in comments.items():
                                st.write(f"**{member}:**")
                                for cmnt in comments_list:
                                    st.text(f"- {cmnt}")
            else:
                col1.warning("No data found for this email.")

    def received_tab(self):
        col1, col2 = st.columns([1, 2], border=True)
        with col1:
            sender_email = st.text_input("Enter sender's email")
            receiver_email = st.text_input("Enter your email")
            selected_date = st.date_input("Select Collaboration Date")

        if sender_email and receiver_email and selected_date:
            received_data = list(self.collection.find({
                "sender": sender_email,
                "team members": {"$in": [receiver_email]},
                "date": str(selected_date)
            }))

            if received_data:
                team_options = [f"Team {idx + 1}" for idx in range(len(received_data))]
                selected_team = col1.radio("Teams you are part of", team_options)

                if selected_team:
                    team_index = int(selected_team.split()[1]) - 1
                    with col2:
                        team_info = received_data[team_index]
                        st.subheader(f"Data received from {sender_email}")

                        for key, value in team_info.items():
                            if key.startswith("data_"):
                                st.subheader(value['key'],divider='blue')
                                st.text(value['description'])
                                st.dataframe(pd.DataFrame(value['data']))

                        # Comment Section
                        st.markdown("### Add a Comment")
                        comment = st.text_area("Write your comment")
                        if st.button("Submit Comment", use_container_width=True):
                            if comment.strip():
                                comments = team_info.get("comments", {})
                                if receiver_email in comments:
                                    comments[receiver_email].append(comment)
                                else:
                                    comments[receiver_email] = [comment]

                                self.collection.update_one(
                                    {"_id": team_info["_id"]},
                                    {"$set": {"comments": comments}}
                                )
                                st.success("Comment added successfully!")
                            else:
                                st.warning("Please enter a valid comment.")
                        else:
                            st.text("No comments available.")

            else:
                col1.warning("No data found matching this combination.")
collab = Collaboration()
collab.display()
