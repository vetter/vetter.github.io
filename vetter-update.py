#!/usr/bin/env python3
"""
Google Sheets to Jekyll Academic Pages Importer
Imports talks, service, and software data from Google Sheets into Jekyll markdown files.
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import yaml
from datetime import datetime
import os
import re
from pathlib import Path

class AcademicPagesImporter:
    def __init__(self, credentials_file, spreadsheet_url):
        """Initialize with Google Sheets credentials and spreadsheet URL"""
        self.spreadsheet_url = spreadsheet_url
        
        # Set up Google Sheets API
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
        self.client = gspread.authorize(creds)
        
        # Open the spreadsheet
        self.sheet = self.client.open_by_url(spreadsheet_url)
    
    def clean_filename(self, text):
        """Convert text to a clean filename"""
        # Remove special characters and convert to lowercase
        filename = re.sub(r'[^\w\s-]', '', text.lower())
        filename = re.sub(r'[-\s]+', '-', filename)
        return filename.strip('-')
    
    def import_talks(self, worksheet_name="Talks"):
        """Import talks from Google Sheet to _talks/ directory"""
        print(f"Importing talks from '{worksheet_name}' worksheet...")
        
        try:
            worksheet = self.sheet.worksheet(worksheet_name)
            data = worksheet.get_all_records()
        except gspread.WorksheetNotFound:
            print(f"Worksheet '{worksheet_name}' not found!")
            return
        
        # Create _talks directory if it doesn't exist
        talks_dir = Path("_talks")
        talks_dir.mkdir(exist_ok=True)
        
        for row in data:
            if not row.get('title'):  # Skip empty rows
                continue
                
            # Extract data from row
            title = row.get('title', '')
            talk_type = row.get('type', 'Talk')  # Talk, Keynote, Panel, etc.
            venue = row.get('venue', '')
            location = row.get('location', '')
            date_str = row.get('date', '')
            description = row.get('description', '')
            slides_url = row.get('slides_url', '')
            video_url = row.get('video_url', '')
            
            # Parse date
            try:
                if date_str:
                    date_obj = pd.to_datetime(date_str)
                    date_formatted = date_obj.strftime('%Y-%m-%d')
                else:
                    date_formatted = datetime.now().strftime('%Y-%m-%d')
            except:
                date_formatted = datetime.now().strftime('%Y-%m-%d')
            
            # Create filename
            filename = f"{date_formatted}-{self.clean_filename(title)}.md"
            filepath = talks_dir / filename
            
            # Create front matter
            front_matter = {
                'title': title,
                'collection': 'talks',
                'type': talk_type,
                'permalink': f"/talks/{date_formatted[:4]}-{self.clean_filename(title)}",
                'venue': venue,
                'date': date_formatted,
                'location': location
            }
            
            # Create content
            content = f"---\n{yaml.dump(front_matter, default_flow_style=False)}---\n\n"
            
            if description:
                content += f"{description}\n\n"
            
            if slides_url:
                content += f"[Download slides]({slides_url})\n\n"
            
            if video_url:
                content += f"[Watch video]({video_url})\n"
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Created: {filepath}")
        
        print(f"Talks import completed!")
    
    def import_service(self, worksheet_name="Service"):
        """Import service activities to _pages/service.md"""
        print(f"Importing service from '{worksheet_name}' worksheet...")
        
        try:
            worksheet = self.sheet.worksheet(worksheet_name)
            data = worksheet.get_all_records()
        except gspread.WorksheetNotFound:
            print(f"Worksheet '{worksheet_name}' not found!")
            return
        
        # Group service by category
        service_categories = {}
        for row in data:
            if not row.get('activity'):  # Skip empty rows
                continue
                
            category = row.get('category', 'Other')
            if category not in service_categories:
                service_categories[category] = []
            
            service_categories[category].append({
                'activity': row.get('activity', ''),
                'organization': row.get('organization', ''),
                'years': row.get('years', ''),
                'description': row.get('description', '')
            })
        
        # Create service page content
        content = """---
layout: archive
title: "Service"
permalink: /service/
author_profile: true
---

"""
        
        for category, activities in service_categories.items():
            content += f"## {category}\n\n"
            
            for activity in activities:
                content += f"* **{activity['activity']}**"
                
                if activity['organization']:
                    content += f", {activity['organization']}"
                
                if activity['years']:
                    content += f" ({activity['years']})"
                
                content += "\n"
                
                if activity['description']:
                    content += f"  {activity['description']}\n"
                
                content += "\n"
        
        # Write service page
        service_file = Path("_pages/service.md")
        with open(service_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Service page updated: {service_file}")
    
    def import_software(self, worksheet_name="Software"):
        """Import software/tools to _portfolio/ directory"""
        print(f"Importing software from '{worksheet_name}' worksheet...")
        
        try:
            worksheet = self.sheet.worksheet(worksheet_name)
            data = worksheet.get_all_records()
        except gspread.WorksheetNotFound:
            print(f"Worksheet '{worksheet_name}' not found!")
            return
        
        # Create _portfolio directory if it doesn't exist
        portfolio_dir = Path("_portfolio")
        portfolio_dir.mkdir(exist_ok=True)
        
        for i, row in enumerate(data):
            if not row.get('name'):  # Skip empty rows
                continue
            
            # Extract data
            name = row.get('name', '')
            description = row.get('description', '')
            github_url = row.get('github_url', '')
            project_url = row.get('project_url', '')
            documentation_url = row.get('documentation_url', '')
            language = row.get('language', '')
            status = row.get('status', 'Active')  # Active, Archived, etc.
            
            # Create filename
            filename = f"software-{i+1:02d}-{self.clean_filename(name)}.md"
            filepath = portfolio_dir / filename
            
            # Create front matter
            front_matter = {
                'title': name,
                'excerpt': description[:100] + "..." if len(description) > 100 else description,
                'collection': 'portfolio',
                'permalink': f"/portfolio/{self.clean_filename(name)}"
            }
            
            # Create content
            content = f"---\n{yaml.dump(front_matter, default_flow_style=False)}---\n\n"
            content += f"## {name}\n\n"
            
            if description:
                content += f"{description}\n\n"
            
            if language:
                content += f"**Language/Technology:** {language}\n\n"
            
            if status:
                content += f"**Status:** {status}\n\n"
            
            # Add links
            links = []
            if github_url:
                links.append(f"[GitHub Repository]({github_url})")
            if project_url:
                links.append(f"[Project Website]({project_url})")
            if documentation_url:
                links.append(f"[Documentation]({documentation_url})")
            
            if links:
                content += "**Links:** " + " | ".join(links) + "\n\n"
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Created: {filepath}")
        
        print(f"Software import completed!")
    
    def import_all(self):
        """Import all data from Google Sheets"""
        print("Starting import from Google Sheets...")
        print("=" * 50)
        
        self.import_talks()
        print()
        self.import_service()
        print()
        self.import_software()
        print()
        
        print("All imports completed!")
        print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function to run the importer"""
    
    # Configuration
    CREDENTIALS_FILE = "google_credentials.json"  # Download from Google Cloud Console
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: Credentials file '{CREDENTIALS_FILE}' not found!")
        print("\nTo set up Google Sheets API access:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Google Sheets API")
        print("4. Create service account credentials")
        print("5. Download JSON key file as 'google_credentials.json'")
        print("6. Share your Google Sheet with the service account email")
        return
    
    try:
        importer = AcademicPagesImporter(CREDENTIALS_FILE, SPREADSHEET_URL)
        importer.import_all()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your Google Sheet is shared with the service account email")
        print("and the spreadsheet URL is correct.")

if __name__ == "__main__":
    main()

