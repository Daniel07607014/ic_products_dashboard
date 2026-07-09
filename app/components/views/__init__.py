"""Reusable page-view render functions.

Each ``render_*`` here draws one logical sub-view. Consolidated pages
under ``app/pages/`` compose these via ``st.tabs`` so the sidebar stays
small while the sub-views remain individually maintainable.
"""
