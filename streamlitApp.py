import streamlit as st
import pandas as pd
from pymongo import MongoClient
from PIL import Image
import io
import base64

class ViewCollaborations:
    def __init__(self):
        self.client = None
        self.db = None
        self.initialize_session()
        
    def initialize_session(self):
        if 'db_connected' not in st.session_state:
            st.session_state.db_connected = False
    
    def show_interface(self):
        self._show_sidebar()
        
        if st.session_state.db_connected:
            tab1, tab2 = st.tabs(["View Data", "Make Complaint"])
            with tab1:
                self._show_view_data_tab()
            with tab2:
                self._show_make_complaint_tab()
        else:
            st.warning("Please connect to a database first")
    
    def _show_sidebar(self):
        with st.sidebar:
            st.header("Database Connection")
            db_name = st.text_input("Database Name", key="db_name_input")
            password = st.text_input("Password", type="password", key="db_password_input")
            
            if st.button("Connect", key="connect_button"):
                self._connect_database(db_name, password)
    
    def _connect_database(self, db_name, password):
        if not db_name:
            st.error("Please enter a database name")
            return
            
        try:
            self.client = MongoClient(st.secrets['database']['link'])
            
            # Check if database exists
            if db_name not in self.client.list_database_names():
                st.error(f"No database exists with name: {db_name}")
                return
                
            self.db = self.client[db_name]
            auth_collection = self.db['Authenticator']
            auth_doc = auth_collection.find_one()
            
            if not auth_doc or auth_doc.get('password') != password:
                st.error("Wrong password entered - contact administrator")
                return
                
            st.session_state.db_connected = True
            st.success("Connected to database successfully")
            
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            st.session_state.db_connected = False
    
    def _show_view_data_tab(self):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            try:
                collections = [col for col in self.db.list_collection_names() if col != 'Authenticator']
                if not collections:
                    st.warning("No collections available")
                    return
                    
                selected_collection = st.selectbox("Select Collection", collections)
                view_option = st.radio("View Option", ["View Selected", "View All"])
            
            except Exception as e:
                st.error(f"Error accessing collections: {str(e)}")
                return
        
        with col2:
            if view_option == "View Selected":
                self._show_selected_document(selected_collection)
            else:
                self._show_all_documents(selected_collection)
    
    def _show_selected_document(self, collection_name):
        try:
            docs = list(self.db[collection_name].find({}, {'key': 1}))
            if not docs:
                st.warning("No documents found")
                return
                
            selected_key = st.selectbox("Select Key", [doc['key'] for doc in docs])
            doc = self.db[collection_name].find_one({'key': selected_key})
            
            st.write(f"**Key:** {doc.get('key', 'N/A')}")
            st.write(f"**Description:** {doc.get('description', 'None')}")
            
            if 'data' in doc:
                st.dataframe(pd.DataFrame(doc['data']))
            elif 'image' in doc:
                st.image(base64.b64decode(doc['image']), use_column_width=True)
                
        except Exception as e:
            st.error(f"Error showing document: {str(e)}")
    
    def _show_all_documents(self, collection_name):
        try:
            docs = list(self.db[collection_name].find())
            if not docs:
                st.warning("No documents found")
                return
                
            for doc in docs:
                st.write(f"**Key:** {doc.get('key', 'N/A')}")
                st.write(f"**Description:** {doc.get('description', 'None')}")
                
                if 'data' in doc:
                    st.dataframe(pd.DataFrame(doc['data']))
                elif 'image' in doc:
                    st.image(base64.b64decode(doc['image']), use_column_width=True)
                
                st.divider()
                
        except Exception as e:
            st.error(f"Error showing documents: {str(e)}")
    
    def _show_make_complaint_tab(self):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            try:
                collections = [col for col in self.db.list_collection_names() if col != 'Authenticator']
                if not collections:
                    st.warning("No collections available")
                    return
                    
                selected_collection = st.selectbox("Select Collection", collections, key="complaint_collection")
                docs = list(self.db[selected_collection].find({}, {'key': 1}))
                
                if not docs:
                    st.warning("No documents in collection")
                    return
                    
                selected_key = st.selectbox("Select Document", [doc['key'] for doc in docs], key="complaint_doc")
            
            except Exception as e:
                st.error(f"Error preparing complaint form: {str(e)}")
                return
        
        with col2:
            name = st.text_input("Your Name")
            complaint_text = st.text_area("Complaint Details")
            
            if st.button("Submit Complaint"):
                if not name or not complaint_text:
                    st.error("Please fill all fields")
                    return
                    
                try:
                    complaint = {
                        'id_number': f"comp_{pd.Timestamp.now().value}",
                        'name': name,
                        'collection': selected_collection,
                        'complaint_on': selected_key,
                        'complaint': complaint_text
                    }
                    
                    if 'complaints' not in self.db.list_collection_names():
                        self.db.create_collection('complaints')
                    
                    self.db['complaints'].insert_one(complaint)
                    st.success("Complaint submitted successfully")
                    
                except Exception as e:
                    st.error(f"Failed to submit complaint: {str(e)}")

def main():
    st.title("Collaboration Data Viewer")
    viewer = ViewCollaborations()
    viewer.show_interface()

if __name__ == "__main__":
    main()
