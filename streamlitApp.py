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
        if 'database' not in st.session_state:
            st.session_state.database = None
        if 'allData' not in st.session_state:
            st.session_state.allData = {'sample': pd.DataFrame()}
    
    def show_interface(self):
        self._show_sidebar()
        
        if st.session_state.database:
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
    
    def _connect_database(self, db_name: str, password: str):
        if not db_name:
            st.error("Please enter a database name")
            return
            
        try:
            self.client = MongoClient(st.secrets['database']['link'])
            
            # Check if database exists first
            if db_name not in self.client.list_database_names():
                st.error(f"No database exists with name: {db_name}")
                return
                
            db = self.client[db_name]
            authenticator = db['Authenticator']
            
            # Verify password
            auth_doc = authenticator.find_one()
            if not auth_doc:
                st.error("Database configuration error - contact administrator")
                return
                
            if auth_doc.get('password') != password:
                st.error("Wrong password entered - contact administrator")
                return
                
            st.session_state.database = db
            st.success("Connected to database successfully")
            
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
    
    def _show_view_data_tab(self):
        col1, col2 = st.columns([1, 2], border=True)
        
        with col1:
            collections = self._get_collections()
            if not collections:
                st.warning("No collections available")
                return
                
            selected_collection = st.selectbox(
                "Select Collection", 
                collections, 
                key="view_collection_select"
            )
            view_option = st.radio(
                "View Option", 
                ["View Selected", "View All"],
                key="view_option_radio"
            )
        
        with col2:
            if view_option == "View Selected":
                self._show_selected_document(selected_collection)
            else:
                self._show_all_documents(selected_collection)
    
    def _show_make_complaint_tab(self):
        col1, col2 = st.columns([1, 2], border=True)
        
        with col1:
            collections = self._get_collections()
            if not collections:
                st.warning("No collections available")
                return
                
            selected_collection = st.selectbox(
                "Select Collection", 
                collections, 
                key="complaint_collection_select"
            )
            
            if selected_collection:
                documents = self._get_documents(selected_collection)
                if not documents:
                    st.warning("No documents in this collection")
                    return
                    
                selected_key = st.selectbox(
                    "Select Document", 
                    [doc['key'] for doc in documents],
                    key="complaint_key_select"
                )
        
        with col2:
            if selected_collection and selected_key:
                self._show_complaint_form(selected_collection, selected_key)
    
    def _show_selected_document(self, collection_name: str):
        st.subheader("View Document")
        documents = self._get_documents(collection_name)
        if not documents:
            st.warning("No documents found")
            return
            
        selected_key = st.selectbox(
            "Select Key", 
            [doc['key'] for doc in documents],
            key=f"select_key_{collection_name}"
        )
        
        if selected_key:
            doc = self._get_document(collection_name, selected_key)
            self._display_document(doc)
    
    def _show_all_documents(self, collection_name: str):
        st.subheader("All Documents")
        documents = self._get_documents(collection_name)
        if not documents:
            st.warning("No documents found")
            return
            
        for doc in documents:
            self._display_document(doc)
            st.divider()
    
    def _show_complaint_form(self, collection_name: str, document_key: str):
        st.subheader("Create Complaint")
        
        name = st.text_input("Your Name", key="complaint_name")
        complaint_text = st.text_area("Complaint Details", key="complaint_text")
        
        if st.button("Submit Complaint", key="submit_complaint_button"):
            if not name or not complaint_text:
                st.error("Please fill all fields")
                return
                
            try:
                complaint_id = f"comp_{pd.Timestamp.now().value}"
                complaint = {
                    'id_number': complaint_id,
                    'name': name,
                    'collection': collection_name,
                    'complaint_on': document_key,
                    'complaint': complaint_text
                }
                
                if 'complaints' not in st.session_state.database.list_collection_names():
                    st.session_state.database.create_collection('complaints')
                
                st.session_state.database['complaints'].insert_one(complaint)
                st.success("Complaint submitted successfully")
            except Exception as e:
                st.error(f"Failed to submit complaint: {str(e)}")
    
    def _display_document(self, doc: dict):
        if not doc:
            return
            
        st.write(f"**Key:** {doc.get('key', 'N/A')}")
        st.write(f"**Description:** {doc.get('description', 'No description')}")
        
        if 'data' in doc:
            st.dataframe(pd.DataFrame(doc['data']))
        elif 'image' in doc:
            img_bytes = base64.b64decode(doc['image'])
            st.image(img_bytes, use_column_width=True)
            st.write(f"**Format:** {doc.get('image_format', 'Unknown')}")
    
    def _get_collections(self) -> list:
        if not st.session_state.database:
            return []
            
        collections = [
            col for col in st.session_state.database.list_collection_names() 
            if col != 'Authenticator'
        ]
        return collections
    
    def _get_documents(self, collection_name: str) -> list:
        if not st.session_state.database:
            return []
            
        try:
            return list(st.session_state.database[collection_name].find({}, {'key': 1}))
        except Exception as e:
            st.error(f"Error fetching documents: {str(e)}")
            return []
    
    def _get_document(self, collection_name: str, key: str) -> dict:
        if not st.session_state.database:
            return {}
            
        try:
            return st.session_state.database[collection_name].find_one({'key': key})
        except Exception as e:
            st.error(f"Error fetching document: {str(e)}")
            return {}

def main():
    st.title("Collaboration Data Viewer")
    viewer = ViewCollaborations()
    viewer.show_interface()

if __name__ == "__main__":
    main()
