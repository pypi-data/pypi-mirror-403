"""
Streamlit Breadcrumbs Component

A customizable breadcrumb navigation component for Streamlit applications with optional favorite icon.

Example usage:
    breadcrumbs = [
        {"title": "HOME"},
        {"title": "DATA TOOLS HUB", "link": "data_tools_hub"},
        {"title": "MACHINE 360", "link": "machine_360"}
    ]
    
    clicked = st_breadcrumbs(breadcrumbs, is_favorite=False)
    if clicked:
        if clicked.get('link'):
            st.write(f"Navigated to: {clicked['link']}")
        if clicked.get('favorite_clicked'):
            st.write("Favorite was clicked!")
"""

import os
import json
import streamlit.components.v1 as components
from typing import Optional, Callable, Any, List, Dict

# Create the _RELEASE constant
_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "st_breadcrumbs",
        url="http://localhost:3000",
    )
else:
    # When we're distributing a production version of the component.
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_breadcrumbs", path=build_dir)

def st_breadcrumbs(
    items,
    is_favorite: bool = False,
    key=None,
    on_click: Optional[Callable[..., Any]] = None,
    on_favorite_click: Optional[Callable[..., Any]] = None,
    args: Optional[List] = None,
    kwargs: Optional[Dict] = None,
):
    """
    Display a breadcrumb navigation component with optional favorite icon.
    
    Parameters
    ----------
    items : list of dict
        A list of dictionaries where each dictionary represents a breadcrumb item.
        Each item should have a 'title' key and an optional 'link' key.
        Example: [{"title": "HOME"}, {"title": "Page", "link": "page"}]
    is_favorite : bool, optional
        Whether the favorite star should be filled (True) or unfilled (False).
        Default is False.
    key : str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.
    on_click : callable, optional
        A callback function that will be called when a breadcrumb is clicked.
        If provided, this will override the URL navigation.
    on_favorite_click : callable, optional
        A callback function that will be called when the favorite star is clicked.
    args : list, optional
        Additional arguments to pass to the on_click callback function.
    kwargs : dict, optional
        Additional keyword arguments to pass to the on_click callback function.
        
    Returns
    -------
    dict or None
        A dictionary containing click information:
        - 'link': The clicked breadcrumb link (if any)
        - 'favorite_clicked': True if favorite was clicked
        Returns None if no interaction occurred.
    """
    # Validate items
    if not isinstance(items, list):
        raise ValueError("'items' must be a list of dictionaries")
        
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each item in 'items' must be a dictionary")
        if 'title' not in item:
            raise ValueError("Each item must have a 'title' key")
     # Handle the on_click callbacks
    breadcrumb_callback = None
    favorite_callback = None
    
    if callable(on_click):
        args = args or []
        kwargs = kwargs or {}
        
        # Create a callback that accepts Streamlit's argument but ignores it
        def create_breadcrumb_callback(callback, *cb_args, **cb_kwargs):
            def wrapper(_=None):
                return callback(*cb_args, **cb_kwargs)
            return wrapper
        breadcrumb_callback = create_breadcrumb_callback(on_click, *args, **kwargs)
    
    if callable(on_favorite_click):
        def create_favorite_callback(callback):
            def wrapper(_=None):
                return callback()
            return wrapper
        favorite_callback = create_favorite_callback(on_favorite_click)
    
    # Call through to the component.
    component_value = _component_func(
        items=items,
        is_favorite=is_favorite,
        key=str(key),
        default=None,
        on_change=breadcrumb_callback if callable(breadcrumb_callback) else None,
    )
    
    # Handle component return value
    if component_value:
        result = {}
        
        # Handle breadcrumb click
        if component_value.get('link'):
            result['link'] = component_value['link']
            # Trigger breadcrumb callback if provided
            if callable(breadcrumb_callback):
                breadcrumb_callback()
        
        # Handle favorite click
        if component_value.get('favorite_clicked'):
            result['favorite_clicked'] = True
            # Trigger favorite callback if provided
            if callable(favorite_callback):
                favorite_callback()
        
        return result if result else None
    
    return None

