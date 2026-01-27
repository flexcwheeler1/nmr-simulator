#!/usr/bin/env python3
"""
Advanced SDBS integration using proper ASP.NET form handling.
"""

import requests
from bs4 import BeautifulSoup
import re
import time

class AdvancedSDBS:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.base_url = "https://sdbs.db.aist.go.jp"
        self.viewstate = None
        self.viewstate_generator = None
        self.event_validation = None
    
    def _get_form_data(self, soup):
        """Extract ASP.NET form data from the page."""
        form_data = {}
        
        # Get viewstate and other ASP.NET hidden fields
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        if viewstate:
            form_data['__VIEWSTATE'] = viewstate.get('value', '')
        
        viewstate_gen = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        if viewstate_gen:
            form_data['__VIEWSTATEGENERATOR'] = viewstate_gen.get('value', '')
        
        event_val = soup.find('input', {'name': '__EVENTVALIDATION'})
        if event_val:
            form_data['__EVENTVALIDATION'] = event_val.get('value', '')
        
        return form_data
    
    def initialize_session(self):
        """Initialize session and get main page with form data."""
        try:
            main_url = f"{self.base_url}/sdbs/cgi-bin/cre_index.cgi"
            response = self.session.get(main_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            form_data = self._get_form_data(soup)
            
            print(f"Session initialized. ViewState length: {len(form_data.get('__VIEWSTATE', ''))}")
            return form_data, soup
            
        except Exception as e:
            print(f"Error initializing session: {e}")
            return None, None
    
    def search_compound(self, compound_name):
        """Search for a compound using proper ASP.NET form submission."""
        
        # Step 1: Initialize session
        form_data, soup = self.initialize_session()
        if not form_data:
            return []
        
        # Step 2: Check if we need to accept disclaimer first
        disclaimer_button = soup.find('input', {'name': re.compile(r'DisclaimeraAccept')})
        if disclaimer_button:
            print("Accepting disclaimer...")
            
            form_data['__EVENTTARGET'] = ''
            form_data['__EVENTARGUMENT'] = ''
            form_data[disclaimer_button.get('name')] = disclaimer_button.get('value', 'Accept')
            
            try:
                response = self.session.post(f"{self.base_url}/sdbs/cgi-bin/cre_index.cgi", 
                                           data=form_data, timeout=15)
                response.raise_for_status()
                
                # Parse the new page after disclaimer
                soup = BeautifulSoup(response.content, 'html.parser')
                form_data = self._get_form_data(soup)
                print("Disclaimer accepted, proceeding with search...")
                
            except Exception as e:
                print(f"Error accepting disclaimer: {e}")
                return []
        
        # Step 3: Now try to perform the actual search
        # Look for compound name input field
        company_name_field = soup.find('input', {'name': re.compile(r'companame')})
        
        if company_name_field:
            field_name = company_name_field.get('name')
            print(f"Found search field: {field_name}")
            
            # Prepare search form data
            search_data = form_data.copy()
            search_data[field_name] = compound_name
            
            # Add search button trigger
            search_button = soup.find('input', {'type': 'submit', 'value': re.compile(r'[Ss]earch|検索')})
            if search_button:
                search_data[search_button.get('name')] = search_button.get('value')
            
            try:
                print(f"Searching for '{compound_name}'...")
                response = self.session.post(f"{self.base_url}/sdbs/cgi-bin/cre_index.cgi",
                                           data=search_data, timeout=15)
                response.raise_for_status()
                
                # Parse search results
                results_soup = BeautifulSoup(response.content, 'html.parser')
                
                print(f"Search response length: {len(response.text)} characters")
                
                # Save the response for inspection
                with open(f'sdbs_search_result_{compound_name}.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"Saved search result to sdbs_search_result_{compound_name}.html")
                
                # Parse results
                return self._parse_search_results(results_soup)
                
            except Exception as e:
                print(f"Error performing search: {e}")
                return []
        
        else:
            print("Could not find compound name input field")
            return []
    
    def _parse_search_results(self, soup):
        """Parse search results from SDBS response."""
        results = []
        
        # Look for result tables or compound listings
        # SDBS results might be in various formats
        
        # Pattern 1: Look for links with SDBS numbers
        sdbs_links = soup.find_all('a', href=re.compile(r'sdbsno='))
        for link in sdbs_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            sdbs_match = re.search(r'sdbsno=([^&]+)', href)
            if sdbs_match:
                results.append({
                    'name': text,
                    'sdbs_id': sdbs_match.group(1),
                    'url': href if href.startswith('http') else f"{self.base_url}{href}"
                })
        
        # Pattern 2: Look for result tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    # Check for compound links in cells
                    for cell in cells:
                        link = cell.find('a', href=re.compile(r'sdbsno='))
                        if link:
                            href = link.get('href', '')
                            text = link.get_text(strip=True)
                            
                            sdbs_match = re.search(r'sdbsno=([^&]+)', href)
                            if sdbs_match and text not in [r['name'] for r in results]:
                                results.append({
                                    'name': text,
                                    'sdbs_id': sdbs_match.group(1),
                                    'url': href if href.startswith('http') else f"{self.base_url}{href}"
                                })
        
        print(f"Found {len(results)} results")
        return results

def test_advanced_sdbs():
    """Test the advanced SDBS integration."""
    sdbs = AdvancedSDBS()
    
    test_compounds = ["indole", "benzene", "ethanol"]
    
    for compound in test_compounds:
        print(f"\n=== Testing search for: {compound} ===")
        results = sdbs.search_compound(compound)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['name']} (ID: {result['sdbs_id']})")
            print(f"   URL: {result['url']}")

if __name__ == "__main__":
    test_advanced_sdbs()
