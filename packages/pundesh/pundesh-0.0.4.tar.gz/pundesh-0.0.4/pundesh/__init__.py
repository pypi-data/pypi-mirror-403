"""
Automation Toolkit

Includes:

1) GMaps Scraper
   - Google Maps Business Data Extractor

2) EB Review Automation
   - Electronics Bazaar Review Submission Tool

Works in Google Colab and locally.

Quick Start (Google Colab):

    from automation_toolkit import setup_colab, scrape_maps, submit_reviews

    # Run setup first (only once per session)
    await setup_colab()

    # Scrape Google Maps
    df_maps = await scrape_maps("restaurants in New York", max_results=50)

    # Submit Electronics Bazaar reviews
    df_reviews = await submit_reviews(
        "reviews.csv",
        email="your@email.com",
        password="your_password"
    )
"""

# Import everything from the single combined module
from .pundesh import (
    # =========================
    # Google Maps Scraper
    # =========================
    scrape_maps,
    scrape_maps_sync,
    GoogleMapsScraper,
    ScraperConfig,
    Business,
    BusinessList,
    ProxyManager,

    # =========================
    # EB Review Automation
    # =========================
    submit_reviews,
    submit_reviews_sync,
    EBReviewAutomation,
    ReviewConfig,
    ReviewResult,
    ReviewResultList,

    # =========================
    # Shared setup & utilities
    # =========================
    setup_colab,
    install_playwright_deps,
    is_colab,
    is_jupyter,
)

# Package metadata
__version__ = "1.0.0"
__author__ = "Sidharth"

# Public API
__all__ = [

    # ---- Maps scraper ----
    "scrape_maps",
    "scrape_maps_sync",
    "GoogleMapsScraper",
    "ScraperConfig",
    "Business",
    "BusinessList",
    "ProxyManager",

    # ---- Review automation ----
    "submit_reviews",
    "submit_reviews_sync",
    "EBReviewAutomation",
    "ReviewConfig",
    "ReviewResult",
    "ReviewResultList",

    # ---- Setup & utils ----
    "setup_colab",
    "install_playwright_deps",
    "is_colab",
    "is_jupyter",
]

