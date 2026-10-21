"""The map's short country names. Kept free of numpy and PIL: the publisher's title check imports the writer
through this, and the publisher runs without the drawing stack."""
from __future__ import annotations

SHORT_NAMES = {"United Arab Emirates": "UAE", "People's Republic of China": "China",
               "United States of America": "USA", "United Kingdom": "UK", "Russian Federation": "Russia",
               "Democratic Republic of the Congo": "DR Congo", "Republic of the Congo": "Congo",
               "Central African Republic": "C. African Rep.", "Bosnia and Herzegovina": "Bosnia",
               "Dominican Republic": "Dominican Rep.", "Papua New Guinea": "Papua N. Guinea",
               "Trinidad and Tobago": "Trinidad & Tobago", "Saint Vincent and the Grenadines": "St Vincent",
               "Republic of China": "Taiwan", "South Korea": "South Korea", "North Korea": "North Korea"}


def short_name(name: str) -> str:
    return SHORT_NAMES.get(name, name)
