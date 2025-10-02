#!/usr/bin/env python3
"""
Import service activities from Google Sheets to Jekyll Academic Pages format.
Creates markdown files in _service/ directory.
"""

import pandas as pd
import requests
import yaml
from datetime import datetime
from pathlib import Path
import re
from io import StringIO

# CONFIGURATION - UPDATE WITH YOUR GOOGLE SHEET INFO
SPREADSHEET_ID = "14MUqC_7MRgSj5RUkMYuIczd4F9v6Zd2Klq-E5x2LJAk"
SHEET_NAME = "service"  # Name of your service sheet

# Trivial words to skip when creating filenames
TRIVIAL_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'should', 'could', 'may', 'might', 'must', 'can', 'about'
}

def get_public_sheet_data(spreadsheet_id, sheet_name):
    """Download data from public Google Sheet as pandas DataFrame"""
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        print(f"✓ Loaded {len(df)} service activities from Google Sheets")
        return df
    except requests.RequestException as e:
        print(f"✗ Error fetching data: {e}")
        print(f"   Make sure the sheet '{sheet_name}' exists and is publicly accessible")
        return pd.DataFrame()

def safe_get(row, column, default=""):
    """Safely get value from row, handling NaN and missing columns"""
    if column not in row:
        return default
    value = row[column]
    return default if pd.isna(value) else str(value).strip()

def get_first_nontrivial_word(title):
    """Extract first non-trivial word from title for filename"""
    if not title:
        return "service"
    
    # Remove special characters and split into words
    words = re.sub(r'[^\w\s-]', '', title.lower()).split()
    
    # Find first non-trivial word
    for word in words:
        if word and word not in TRIVIAL_WORDS and len(word) > 2:
            return word
    
    # If all words are trivial, just use the first word
    return words[0] if words else "service"

def clean_url_slug(text):
    """Convert text to URL-safe slug"""
    if not text or pd.isna(text):
        return ""
    # Remove special characters, convert to lowercase
    slug = re.sub(r'[^\w\s-]', '', str(text).lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def parse_date(date_str):
    """Parse date string into YYYY-MM-DD format"""
    if not date_str or pd.isna(date_str):
        return None
    
    try:
        # Try to parse with pandas (handles many formats)
        date_obj = pd.to_datetime(date_str)
        return date_obj.strftime('%Y-%m-%d')
    except:
        print(f"   Warning: Could not parse date '{date_str}'")
        return None

def create_date_range(year, end_year):
    """Create date range string from Year and EndYear"""
    if not year:
        return None
    
    # If no end year or same as start year, just use single year
    if not end_year or end_year == year:
        return f"{year}-01-01"
    
    # Multi-year service
    return f"{year}-01-01"

def import_service():
    """Import service activities from Google Sheet to _service/ directory"""
    print("\n" + "="*60)
    print("SERVICE ACTIVITIES IMPORTER")
    print("="*60)
    
    # Fetch data
    df = get_public_sheet_data(SPREADSHEET_ID, SHEET_NAME)
    if df.empty:
        return
    
    # Create _service directory
    service_dir = Path("_service")
    service_dir.mkdir(exist_ok=True)
    
    # Remove existing service files (optional)
    print("\nCleaning up old service files...")
    for existing_file in service_dir.glob("*.md"):
        existing_file.unlink()
        print(f"  Removed: {existing_file.name}")
    
    print("\nCreating service files...")
    created_count = 0
    skipped_count = 0
    
    for idx, row in df.iterrows():
        # Extract core data
        name = safe_get(row, 'Name')
        year = safe_get(row, 'Year')
        
        # Skip rows without name or year
        if not name or not year:
            skipped_count += 1
            print(f"  ⚠ Skipping row {idx + 2}: Missing name or year")
            continue
        
        # Extract other fields
        end_year = safe_get(row, 'EndYear')
        service_type = safe_get(row, 'Type', 'Service')
        leadership = safe_get(row, 'Leadership')
        point_of_contact = safe_get(row, 'PointOfContact')
        url = safe_get(row, 'URL')
        comments = safe_get(row, 'Comments')
        date_str = safe_get(row, 'Date')
        location = safe_get(row, 'Location')
        
        # Create date for sorting (prefer Date field, fall back to Year)
        if date_str:
            date_formatted = parse_date(date_str)
        else:
            date_formatted = create_date_range(year, end_year)
        
        if not date_formatted:
            date_formatted = f"{year}-01-01"
        
        # Create filename: YYYY-MM-DD-word.md
        first_word = get_first_nontrivial_word(name)
        filename = f"{date_formatted}-{first_word}.md"
        
        # Handle duplicate filenames by appending a number
        filepath = service_dir / filename
        counter = 1
        while filepath.exists():
            filename = f"{date_formatted}-{first_word}-{counter}.md"
            filepath = service_dir / filename
            counter += 1
        
        # Create year range display
        if end_year and end_year != year:
            year_display = f"{year}–{end_year}"
        else:
            year_display = year
        
        # Create permalink
        permalink_slug = clean_url_slug(f"{year}-{first_word}")
        permalink = f"/service/{permalink_slug}"
        
        # Build front matter
        front_matter = {
            'title': name,
            'collection': 'service',
            'type': service_type if service_type else 'Service',
            'permalink': permalink,
            'date': date_formatted,
            'year': year_display
        }
        
        if location:
            front_matter['location'] = location
        
        # Create content
        content_lines = []
        content_lines.append("---")
        content_lines.append(yaml.dump(front_matter, default_flow_style=False).strip())
        content_lines.append("---")
        content_lines.append("")
        
        # Add main content
        main_content = []
        
        if service_type:
            main_content.append(f"Type: {service_type}")

        # if leadership:
        #     main_content.append(f"**Role:** {leadership}")
        
        # if point_of_contact:
        #     main_content.append(f"**Point of Contact:** {point_of_contact}")
        
        if url:
            main_content.append(f"[More information]({url})")
        
        # if comments:
        #     main_content.append(f"\n{comments}")
        
        # Add content to file
        if main_content:
            content_lines.append("\n\n".join(main_content))
        else:
            content_lines.append(f"Service activity: {name}")
        
        content_lines.append("")
        
        # Write file
        final_content = "\n".join(content_lines)
        filepath.write_text(final_content, encoding='utf-8')
        
        print(f"  ✓ Created: {filename}")
        created_count += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"✅ Import complete!")
    print(f"   Created: {created_count} service files")
    if skipped_count > 0:
        print(f"   Skipped: {skipped_count} rows (missing data)")
    print("="*60)
    
    print("\nNext steps:")
    print("1. Review files in _service/ directory")
    print("2. Test locally: bundle exec jekyll serve")
    print("3. Commit: git add _service && git commit -m 'Update service activities'")
    print("4. Push: git push origin main")
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function"""
    print("📊 SERVICE ACTIVITIES IMPORTER FROM GOOGLE SHEETS")
    print("="*60)
    
    if SPREADSHEET_ID == "YOUR_SPREADSHEET_ID_HERE":
        print("\n✗ ERROR: Please update SPREADSHEET_ID in the script!")
        print("\nSetup instructions:")
        print("1. Open your Google Sheet")
        print("2. Click Share → 'Anyone with the link can view'")
        print("3. Copy the spreadsheet ID from the URL:")
        print("   https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit")
        print("4. Update SPREADSHEET_ID in this script")
        print("\nExpected columns in your Google Sheet:")
        print("   Year | EndYear | Type | Leadership | Name | PointOfContact")
        print("   URL | Comments | Date | Location")
        return
    
    print(f"📊 Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"📄 Sheet name: {SHEET_NAME}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        import_service()
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("- Verify your Google Sheet is publicly accessible")
        print("- Check that the sheet name matches exactly")
        print("- Ensure required columns (Name, Year) exist")

if __name__ == "__main__":
    main()