"""
Streamlit Favorite Component

A clickable star icon component for Streamlit applications with tooltip support.

Example usage:
    # Display a favorite star
    clicked = st_favorite(is_favorite=False)
    if clicked:
        st.write("Star was clicked!")
    
    # With on_click callback
    def handle_favorite_click():
        st.session_state.is_favorite = not st.session_state.is_favorite
    
    st_favorite(is_favorite=st.session_state.is_favorite, on_click=handle_favorite_click)
"""

import os
import streamlit.components.v1 as components
from typing import Optional, Callable, Any

# Create the _RELEASE constant
_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "st_favorite",
        url="http://localhost:3000",
    )
else:
    # When we're distributing a production version of the component.
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_favorite", path=build_dir)

def st_favorite(
    is_favorite: bool,
    key=None,
    on_click: Optional[Callable[..., Any]] = None,
):
    """
    Display a clickable star icon component.
    
    Parameters
    ----------
    is_favorite : bool
        Whether the star should be filled (True) or unfilled (False).
        This also affects the tooltip text.
    key : str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.
    on_click : callable, optional
        A callback function that will be called when the star is clicked.
        
    Returns
    -------
    bool
        True if the star was clicked, False otherwise.
    """
    # Handle the on_click callback
    if callable(on_click):
        # Create a callback that accepts Streamlit's argument but ignores it
        def create_callback(callback):
            def wrapper(_=None):
                return callback()
            return wrapper
        on_click = create_callback(on_click)
    
    # Call through to the component.
    component_value = _component_func(
        is_favorite=is_favorite,
        key=str(key),
        default=None,
        on_change=on_click if callable(on_click) else None,
    )
    
    # Return True if the star was clicked
    return component_value.get('clicked') if component_value else False

