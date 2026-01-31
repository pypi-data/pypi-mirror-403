"""
Breadcrumbs Component Example

This example demonstrates how to use the st_breadcrumbs component with favorite icon.
"""

import os
import sys
import streamlit as st

# Get the absolute path to the parent directory (rockyroad_tools)
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Insert the path to the rockyroad_tools directory into sys.path
sys.path.insert(0, parent_dir)

def main():
    from streamlit_rockyroad_tools import st_breadcrumbs
    st.set_page_config(page_title="Breadcrumbs Example", layout="wide")
    
    st.title("🧭 Breadcrumbs Navigation with Favorite Icon Example")
    
    # Initialize session state
    if 'is_favorite' not in st.session_state:
        st.session_state.is_favorite = False
    
    if 'navigation_count' not in st.session_state:
        st.session_state.navigation_count = 0
    
    # Example 1: Basic usage with favorite
    st.header("Basic Usage with Favorite Icon")
    st.write("Click on breadcrumbs to navigate or the star to toggle favorite:")
    
    breadcrumbs = [
        {"title": "HOME", "link": "/"},
        {"title": "HELP CENTER", "link": "help_center"},
        {"title": "PORTAL USER DIRECTORY"}
    ]

    def handle_breadcrumb_click():
        st.session_state.navigation_count += 1
        st.toast("Breadcrumb clicked!", icon="🧭")
    
    def handle_favorite_click():
        st.session_state.is_favorite = not st.session_state.is_favorite
        st.toast(f"Page {'added to' if st.session_state.is_favorite else 'removed from'} favorites!", icon="⭐")
    
    result = st_breadcrumbs(
        breadcrumbs, 
        is_favorite=st.session_state.is_favorite,
        key="basic_breadcrumbs",
        on_click=handle_breadcrumb_click,
        on_favorite_click=handle_favorite_click
    )
    
    if result:
        if result.get('link'):
            st.success(f"Navigated to: {result['link']}")
        if result.get('favorite_clicked'):
            st.info("Favorite was clicked!")
    
    st.write(f"Current state: {'⭐ Favorited' if st.session_state.is_favorite else '☆ Not favorited'}")
    st.write(f"Navigation count: {st.session_state.navigation_count}")
    
    st.divider()
    
    # Example 2: Multiple breadcrumb sets
    st.header("Multiple Breadcrumb Sets")
    st.write("Different pages with different favorite states:")
    
    # Initialize states for multiple pages
    pages = [
        {"name": "Dashboard", "items": [{"title": "HOME", "link": "/"}, {"title": "DASHBOARD"}], "state_key": "fav_dashboard"},
        {"name": "Reports", "items": [{"title": "HOME", "link": "/"}, {"title": "REPORTS"}], "state_key": "fav_reports"},
        {"name": "Settings", "items": [{"title": "HOME", "link": "/"}, {"title": "SETTINGS"}], "state_key": "fav_settings"},
    ]
    
    for page in pages:
        if page["state_key"] not in st.session_state:
            st.session_state[page["state_key"]] = False
        
        with st.expander(f"{page['name']} Page"):
            result = st_breadcrumbs(
                page["items"],
                is_favorite=st.session_state[page["state_key"]],
                key=f"breadcrumbs_{page['state_key']}"
            )
            
            if result and result.get('favorite_clicked'):
                st.session_state[page["state_key"]] = not st.session_state[page["state_key"]]
                st.rerun()
            
            st.write(f"Favorite status: {'⭐' if st.session_state[page['state_key']] else '☆'}")
    
    st.divider()
    
    # Example 3: Integration with navigation
    st.header("Navigation Integration")
    st.write("Simulating a real navigation scenario:")
    
    # Current page tracking
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "home"
    
    # Define navigation structure
    nav_structure = {
        "home": {"title": "HOME", "link": "/", "favorite_key": "fav_home"},
        "help_center": {"title": "HELP CENTER", "link": "help_center", "favorite_key": "fav_help_center"},
        "user_directory": {"title": "PORTAL USER DIRECTORY", "link": "user_directory", "favorite_key": "fav_user_directory"},
    }
    
    # Initialize favorite states
    for page_info in nav_structure.values():
        if page_info["favorite_key"] not in st.session_state:
            st.session_state[page_info["favorite_key"]] = False
    
    # Build breadcrumbs based on current page
    if st.session_state.current_page == "home":
        current_breadcrumbs = [{"title": "HOME", "link": "/"}]
        current_favorite_key = "fav_home"
    elif st.session_state.current_page == "help_center":
        current_breadcrumbs = [
            {"title": "HOME", "link": "/"},
            {"title": "HELP CENTER", "link": "help_center"}
        ]
        current_favorite_key = "fav_help_center"
    else:  # user_directory
        current_breadcrumbs = [
            {"title": "HOME", "link": "/"},
            {"title": "HELP CENTER", "link": "help_center"},
            {"title": "PORTAL USER DIRECTORY"}
        ]
        current_favorite_key = "fav_user_directory"
    
    def handle_navigation():
        # This would handle actual navigation in a real app
        pass
    
    def handle_page_favorite():
        st.session_state[current_favorite_key] = not st.session_state[current_favorite_key]
        st.rerun()
    
    result = st_breadcrumbs(
        current_breadcrumbs,
        is_favorite=st.session_state[current_favorite_key],
        key="navigation_breadcrumbs",
        on_click=handle_navigation,
        on_favorite_click=handle_page_favorite
    )
    
    # Display current page info
    st.write(f"**Current Page:** {st.session_state.current_page}")
    st.write(f"**Favorite Status:** {'⭐ Favorited' if st.session_state[current_favorite_key] else '☆ Not favorited'}")
    
    # Page navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Go to Home", key="nav_home"):
            st.session_state.current_page = "home"
            st.rerun()
    with col2:
        if st.button("Go to Help Center", key="nav_help"):
            st.session_state.current_page = "help_center"
            st.rerun()
    with col3:
        if st.button("Go to User Directory", key="nav_user"):
            st.session_state.current_page = "user_directory"
            st.rerun()
    

if __name__ == "__main__":
    main()
