#!/usr/bin/env python3
"""Generate a Leaflet cluster map of talk locations.

Geocodes locations from _presentations/*.md front matter and caches results
in talkmap/geocode_cache.json so repeated runs are fast.
"""

import json
import glob
import os
import time

import frontmatter
from geopy import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut
import getorg


class CachedLocation:
    """Lightweight stand-in for geopy Location with .latitude/.longitude."""

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

CACHE_FILE = "talkmap/geocode_cache.json"
TIMEOUT = 5


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def main():
    geocoder = Nominatim(user_agent="academicpages.github.io")
    geocode = RateLimiter(geocoder.geocode, min_delay_seconds=2, max_retries=3)
    cache = load_cache()
    location_dict = {}

    for file in sorted(glob.glob("_presentations/*.md")):
        data = frontmatter.load(file).to_dict()

        if "location" not in data:
            continue

        title = data["title"].strip()
        venue = data["venue"].strip()
        location = data["location"].strip()
        description = f"{title}<br />{venue}; {location}"

        # Check cache first (keyed by location string)
        if location in cache:
            lat, lon = cache[location]
            location_dict[description] = CachedLocation(lat, lon)
            print(f"  cached: {location} -> ({lat}, {lon})")
            continue

        # Geocode (rate limiter handles delay and retries)
        try:
            result = geocode(location, timeout=TIMEOUT)
            if result:
                cache[location] = (result.latitude, result.longitude)
                location_dict[description] = result
                print(f"  geocoded: {location} -> ({result.latitude}, {result.longitude})")
            else:
                print(f"  warning: no result for {location}")
        except GeocoderTimedOut:
            print(f"  timeout: {location}")
        except Exception as ex:
            print(f"  error: {location} — {ex}")

    save_cache(cache)

    # Generate the map
    m = getorg.orgmap.create_map_obj()
    getorg.orgmap.output_html_cluster_map(
        location_dict, folder_name="talkmap", hashed_usernames=False
    )
    print(f"Done. {len(location_dict)} locations mapped.")


if __name__ == "__main__":
    main()
