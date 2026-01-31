"""
Favorite Component Example

This example demonstrates how to use the st_favorite component.
"""

import os
import sys
import streamlit as st

# Get the absolute path to the parent directory (rockyroad_tools)
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Insert the path to the rockyroad_tools directory into sys.path
sys.path.insert(0, parent_dir)

def main():
    from streamlit_rockyroad_tools import st_favorite
    st.set_page_config(page_title="Favorite Example", layout="wide")
    
    st.title("⭐ Favorite Star Component Example")
    
    # Initialize session state
    if 'is_favorite' not in st.session_state:
        st.session_state.is_favorite = False
    
    if 'click_count' not in st.session_state:
        st.session_state.click_count = 0
    
    # Example 1: Basic usage
    st.header("Basic Usage")
    st.write("Click the star to toggle its state:")
    
    # Display the favorite star
    clicked = st_favorite(is_favorite=st.session_state.is_favorite, key="basic_star")
    
    if clicked:
        st.session_state.is_favorite = not st.session_state.is_favorite
        st.session_state.click_count += 1
        st.rerun()
    
    st.write(f"Current state: {'⭐ Favorited' if st.session_state.is_favorite else '☆ Not favorited'}")
    st.write(f"Times clicked: {st.session_state.click_count}")
    
    st.divider()
    
    # Example 2: With callback function
    st.header("With Callback Function")
    st.write("Using an on_click callback:")
    
    def handle_favorite_click():
        st.session_state.is_favorite = not st.session_state.is_favorite
        st.session_state.click_count += 1
        st.toast(f"Star {'added to' if st.session_state.is_favorite else 'removed from'} favorites!", icon="⭐")
    
    st_favorite(is_favorite=st.session_state.is_favorite, on_click=handle_favorite_click, key="callback_star")
    
    st.divider()
    
    # Example 3: Multiple stars
    st.header("Multiple Stars")
    st.write("Multiple independent favorite stars:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("Item 1")
        if 'fav1' not in st.session_state:
            st.session_state.fav1 = True
        
        if st_favorite(is_favorite=st.session_state.fav1, key="star1"):
            st.session_state.fav1 = not st.session_state.fav1
            st.rerun()
    
    with col2:
        st.write("Item 2")
        if 'fav2' not in st.session_state:
            st.session_state.fav2 = False
        
        if st_favorite(is_favorite=st.session_state.fav2, key="star2"):
            st.session_state.fav2 = not st.session_state.fav2
            st.rerun()
    
    with col3:
        st.write("Item 3")
        if 'fav3' not in st.session_state:
            st.session_state.fav3 = False
        
        if st_favorite(is_favorite=st.session_state.fav3, key="star3"):
            st.session_state.fav3 = not st.session_state.fav3
            st.rerun()
    
    st.divider()
    
    # Example 4: In a data context
    st.header("Data Context Example")
    st.write("Stars in a table-like context:")
    
    items = [
        {"name": "Document A", "favorited": False},
        {"name": "Document B", "favorited": True},
        {"name": "Document C", "favorited": False},
    ]
    
    for i, item in enumerate(items):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(item["name"])
        with col2:
            # Initialize session state for this item if not exists
            state_key = f"item_{i}_fav"
            if state_key not in st.session_state:
                st.session_state[state_key] = item["favorited"]
            
            if st_favorite(is_favorite=st.session_state[state_key], key=f"item_{i}"):
                st.session_state[state_key] = not st.session_state[state_key]
                st.rerun()

if __name__ == "__main__":
    main()
