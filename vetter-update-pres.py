#!/usr/bin/env python3
"""
Import presentations from Google Sheets to Jekyll Academic Pages format.
Creates markdown files in _presentations/ directory.
"""

import pandas as pd
import requests
import yaml
from datetime import datetime
from pathlib import Path
import re
from io import StringIO

# CONFIGURATION - UPDATE WITH YOUR GOOGLE SHEET INFO
# https://docs.google.com/spreadsheets/d/14MUqC_7MRgSj5RUkMYuIczd4F9v6Zd2Klq-E5x2LJAk/edit?usp=sharing
SPREADSHEET_ID = "14MUqC_7MRgSj5RUkMYuIczd4F9v6Zd2Klq-E5x2LJAk"
SHEET_NAME = "presentations"  # Name of your presentations sheet

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
        print(f"✓ Loaded {len(df)} presentations from Google Sheets")
        return df
    except requests.RequestException as e:
        print(f"❌ Error fetching data: {e}")
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
        return "presentation"
    
    # Remove special characters and split into words
    words = re.sub(r'[^\w\s-]', '', title.lower()).split()
    
    # Find first non-trivial word
    for word in words:
        if word and word not in TRIVIAL_WORDS and len(word) > 2:
            return word
    
    # If all words are trivial, just use the first word
    return words[0] if words else "presentation"

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

def create_venue_string(host_org, location):
    """Create venue string from HostOrg and Location"""
    parts = []
    
    if host_org:
        parts.append(host_org)
    
    if location:
        parts.append(location)
    
    return ", ".join(parts) if parts else ""

def import_presentations():
    """Import presentations from Google Sheet to _presentations/ directory"""
    print("\n" + "="*60)
    print("PRESENTATIONS IMPORTER")
    print("="*60)
    
    # Fetch data
    df = get_public_sheet_data(SPREADSHEET_ID, SHEET_NAME)
    if df.empty:
        return
    
    # Create _presentations directory
    presentations_dir = Path("_presentations")
    presentations_dir.mkdir(exist_ok=True)
    
    # Remove existing presentation files (optional)
    print("\nCleaning up old presentation files...")
    for existing_file in presentations_dir.glob("*.md"):
        existing_file.unlink()
        print(f"  Removed: {existing_file.name}")
    
    print("\nCreating presentation files...")
    created_count = 0
    skipped_count = 0
    
    for idx, row in df.iterrows():
        # Extract core data
        title = safe_get(row, 'Title')
        date_str = safe_get(row, 'Date')
        
        # Skip rows without title or date
        if not title or not date_str:
            skipped_count += 1
            print(f"  ⚠ Skipping row {idx + 2}: Missing title or date")
            continue
        
        # Parse date
        date_formatted = parse_date(date_str)
        if not date_formatted:
            skipped_count += 1
            print(f"  ⚠ Skipping '{title}': Invalid date format")
            continue
        
        # Extract other fields
        pres_type = safe_get(row, 'Type', 'Presentation')
        host_org = safe_get(row, 'HostOrg')
        location = safe_get(row, 'Location')
        host_person = safe_get(row, 'HostPerson')
        url = safe_get(row, 'URL')
        contributors = safe_get(row, 'Contributors')
        comments = safe_get(row, 'Comments')
        notes = safe_get(row, 'Notes')
        slides_url = safe_get(row, 'SlidesURL')
        year = safe_get(row, 'Year')
        
        # Create filename: YYYY-MM-DD-word.md
        first_word = get_first_nontrivial_word(title)
        filename = f"{date_formatted}-{first_word}.md"
        
        # Handle duplicate filenames by appending a number
        filepath = presentations_dir / filename
        counter = 1
        while filepath.exists():
            filename = f"{date_formatted}-{first_word}-{counter}.md"
            filepath = presentations_dir / filename
            counter += 1
        
        # Create venue string
        venue = create_venue_string(host_org, location)
        
        # Create permalink
        permalink_slug = clean_url_slug(f"{date_formatted}-{first_word}")
        permalink = f"/presentations/{permalink_slug}"
        
        # Build front matter
        front_matter = {
            'title': title,
            'collection': 'presentations',
            'type': pres_type if pres_type else 'Presentation',
            'permalink': permalink,
            'venue': venue,
            'date': date_formatted,
            'location': location if location else ""
        }
        
        # Create content
        content_lines = []
        content_lines.append("---")
        content_lines.append(yaml.dump(front_matter, default_flow_style=False).strip())
        content_lines.append("---")
        content_lines.append("")
        
        # Add main content (prioritize URL, then comments, then notes)
        main_content = []
        
        if url:
            main_content.append(f"[Presentation materials]({url})")
        
        if slides_url:
            main_content.append(f"[Download slides]({slides_url})")
        
        if comments:
            main_content.append(f"{comments}")
        
        if notes and notes != comments:  # Avoid duplication
            main_content.append(f"{notes}")
        
        # Add content to file
        if main_content:
            content_lines.append("\n\n".join(main_content))
        else:
            content_lines.append("Presentation materials.")
        
        content_lines.append("")
        
        # Add additional metadata as a section (if relevant)
        metadata_lines = []
        
        if host_person:
            metadata_lines.append(f"**Host:** {host_person}")
        
        if contributors:
            metadata_lines.append(f"**Contributors:** {contributors}")
        
        if metadata_lines:
            content_lines.append("")
            content_lines.extend(metadata_lines)
        
        # Write file
        final_content = "\n".join(content_lines)
        filepath.write_text(final_content, encoding='utf-8')
        
        print(f"  ✓ Created: {filename}")
        created_count += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"✅ Import complete!")
    print(f"   Created: {created_count} presentation files")
    if skipped_count > 0:
        print(f"   Skipped: {skipped_count} rows (missing data)")
    print("="*60)
    
    print("\nNext steps:")
    print("1. Review files in _presentations/ directory")
    print("2. Test locally: bundle exec jekyll serve")
    print("3. Commit: git add _presentations && git commit -m 'Update presentations'")
    print("4. Push: git push origin main")
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function"""
    print("📊 PRESENTATIONS IMPORTER FROM GOOGLE SHEETS")
    print("="*60)
    
    if SPREADSHEET_ID == "YOUR_SPREADSHEET_ID_HERE":
        print("\n❌ ERROR: Please update SPREADSHEET_ID in the script!")
        print("\nSetup instructions:")
        print("1. Open your Google Sheet")
        print("2. Click Share → 'Anyone with the link can view'")
        print("3. Copy the spreadsheet ID from the URL:")
        print("   https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit")
        print("4. Update SPREADSHEET_ID in this script")
        print("\nExpected columns in your Google Sheet:")
        print("   Year | Date | Type | HostOrg | Title | Location | HostPerson")
        print("   URL | Contributors | Comments | Printable | Notes | SlidesURL")
        return
    
    print(f"📊 Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"📄 Sheet name: {SHEET_NAME}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        import_presentations()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("- Verify your Google Sheet is publicly accessible")
        print("- Check that the sheet name matches exactly")
        print("- Ensure required columns (Title, Date) exist")

if __name__ == "__main__":
    main()