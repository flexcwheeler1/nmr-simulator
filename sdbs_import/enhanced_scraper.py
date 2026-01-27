"""
Enhanced SDBS Web Scraper for NMR Data

Provides real web scraping functionality for the Spectral Database for Organic Compounds.
Includes demo mode for testing and development.
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Optional, Tuple
import random
from urllib.parse import urljoin, quote


class SDBSScraper:
    """
    Web scraper for SDBS database with real and demo capabilities.
    """
    
    def __init__(self):
        """
        Initialize the SDBS scraper for real web scraping.
        """
        self.base_url = "https://sdbs.db.aist.go.jp"
        self.search_url = f"{self.base_url}/sdbs/cgi-bin/cre_index.cgi"
        
        # Session for maintaining cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 2.0  # Minimum delay between requests in seconds
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to the SDBS server."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def search_compounds(self, compound_name: str, max_results: int = 10) -> List[Dict]:
        """
        Search for compounds in SDBS database - REAL DATA ONLY.
        
        Args:
            compound_name: Name of the compound to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionaries with compound information
        """
        return self._search_compounds_real(compound_name, max_results)
    
    def _search_compounds_real(self, compound_name: str, max_results: int) -> List[Dict]:
        """Real SDBS web search implementation."""
        self._rate_limit()
        
        try:
            # SDBS requires accepting disclaimer first
            disclaimer_url = "https://sdbs.db.aist.go.jp/sdbs/cgi-bin/cre_index.cgi"
            
            # Step 1: Get main page and accept disclaimer
            print(f"Accessing SDBS main page for '{compound_name}'...")
            disclaimer_response = self.session.get(disclaimer_url, timeout=15)
            disclaimer_response.raise_for_status()
            
            disclaimer_soup = BeautifulSoup(disclaimer_response.content, 'html.parser')
            
            # Look for disclaimer accept button
            disclaimer_button = disclaimer_soup.find('input', {'name': re.compile(r'DisclaimeraAccept')})
            
            if disclaimer_button:
                print("Found disclaimer button, accepting terms...")
                
                # Extract ASP.NET form data
                form_data = {}
                
                # Get all hidden fields (ViewState, etc.)
                for hidden_input in disclaimer_soup.find_all('input', {'type': 'hidden'}):
                    name = hidden_input.get('name')
                    value = hidden_input.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Add the disclaimer acceptance button
                form_data[disclaimer_button.get('name')] = disclaimer_button.get('value', 'Accept')
                form_data['__EVENTTARGET'] = ''
                form_data['__EVENTARGUMENT'] = ''
                
                # Submit disclaimer acceptance
                self._rate_limit()
                accept_response = self.session.post(disclaimer_url, data=form_data, timeout=15)
                accept_response.raise_for_status()
                
                print("Disclaimer accepted, accessing search interface...")
                disclaimer_soup = BeautifulSoup(accept_response.content, 'html.parser')
            
            # Step 2: Now perform the actual search
            # Look for the compound name search field
            company_name_field = disclaimer_soup.find('input', {'name': re.compile(r'companame')})
            
            if company_name_field:
                field_name = company_name_field.get('name')
                print(f"Found search field: {field_name}, searching for '{compound_name}'...")
                
                # Extract current form data
                search_form_data = {}
                for hidden_input in disclaimer_soup.find_all('input', {'type': 'hidden'}):
                    name = hidden_input.get('name')
                    value = hidden_input.get('value', '')
                    if name:
                        search_form_data[name] = value
                
                # Add search parameters
                search_form_data[field_name] = compound_name
                search_form_data['__EVENTTARGET'] = ''
                search_form_data['__EVENTARGUMENT'] = ''
                
                # Look for search button
                search_buttons = disclaimer_soup.find_all('input', {'type': 'submit'})
                for button in search_buttons:
                    button_value = button.get('value', '').lower()
                    if 'search' in button_value or '検索' in button_value:
                        search_form_data[button.get('name')] = button.get('value', '')
                        break
                
                # Submit search
                self._rate_limit()
                search_response = self.session.post(disclaimer_url, data=search_form_data, timeout=15)
                search_response.raise_for_status()
                
                print(f"Search submitted, response length: {len(search_response.text)} characters")
                
                # Save search result for debugging
                with open(f'sdbs_search_{compound_name}_result.html', 'w', encoding='utf-8') as f:
                    f.write(search_response.text)
                print(f"Saved search result to sdbs_search_{compound_name}_result.html")
                
                # Parse the search results
                search_soup = BeautifulSoup(search_response.content, 'html.parser')
                results = self._parse_sdbs_search_results(search_soup)
                
                if results:
                    print(f"Found {len(results)} real SDBS results for '{compound_name}'")
                    return results[:max_results]
                else:
                    print(f"No real SDBS results found for '{compound_name}'")
                    return []
            
            else:
                print("Could not find compound name search field")
                return []
            
        except Exception as e:
            print(f"Error in real SDBS search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_sdbs_search_results(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse SDBS search results from HTML."""
        results = []
        
        try:
            # Look for compound links in SDBS format
            # SDBS typically shows results as links with compound names and IDs
            compound_links = soup.find_all('a', href=re.compile(r'direct_frame_top\.cgi\?sdbsno='))
            
            for link in compound_links:
                try:
                    # Extract SDBS number from URL
                    href = link.get('href', '')
                    sdbs_match = re.search(r'sdbsno=([^&]+)', href)
                    
                    if sdbs_match:
                        sdbs_id = sdbs_match.group(1)
                        compound_name = link.get_text(strip=True)
                        
                        # Try to find additional info in the same row/container
                        parent = link.parent
                        if parent:
                            # Look for molecular formula and weight in nearby text
                            parent_text = parent.get_text()
                            
                            # Extract molecular formula (pattern like C8H7N)
                            formula_match = re.search(r'C\d+H\d+[A-Z]*\d*', parent_text)
                            formula = formula_match.group() if formula_match else "Unknown"
                            
                            # Extract molecular weight
                            mw_match = re.search(r'(\d+\.?\d*)\s*g/mol', parent_text)
                            mw = float(mw_match.group(1)) if mw_match else 0
                            
                            results.append({
                                'name': compound_name,
                                'id': sdbs_id,
                                'formula': formula,
                                'mw': mw,
                                'url': f"https://sdbs.db.aist.go.jp/sdbs/cgi-bin/direct_frame_top.cgi?sdbsno={sdbs_id}"
                            })
                
                except Exception as e:
                    continue  # Skip problematic entries
            
            # If no results found with the above method, try alternative parsing
            if not results:
                # Look for table rows that might contain compound data
                table_rows = soup.find_all('tr')
                for row in table_rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # Check if any cell contains an SDBS link
                        for cell in cells:
                            link = cell.find('a', href=re.compile(r'sdbsno='))
                            if link:
                                href = link.get('href', '')
                                sdbs_match = re.search(r'sdbsno=([^&]+)', href)
                                if sdbs_match:
                                    results.append({
                                        'name': link.get_text(strip=True),
                                        'id': sdbs_match.group(1),
                                        'formula': "Unknown",
                                        'mw': 0,
                                        'url': f"https://sdbs.db.aist.go.jp{href}" if href.startswith('/') else href
                                    })
                                    break
        
        except Exception as e:
            print(f"Error parsing SDBS search results: {e}")
        
        return results
    
    def get_nmr_data(self, compound_id: str) -> Dict:
        """
        Get NMR data for a specific compound.
        
        Args:
            compound_id: SDBS compound ID
            
        Returns:
            Dictionary with NMR data
        """
        return self._get_nmr_data_real(compound_id)
    
    def _get_nmr_data_real(self, compound_id: str) -> Dict:
        """Real SDBS NMR data retrieval."""
        self._rate_limit()
        
        try:
            # Construct URL for compound data page
            compound_url = f"https://sdbs.db.aist.go.jp/sdbs/cgi-bin/direct_frame_top.cgi?sdbsno={compound_id}"
            
            response = self.session.get(compound_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            nmr_data = self._parse_real_nmr_data(soup, compound_id)
            
            return nmr_data if nmr_data else {"1H": [], "13C": []}
            
        except requests.RequestException as e:
            print(f"Error retrieving NMR data: {e}")
            return {"1H": [], "13C": []}
        except Exception as e:
            print(f"Unexpected error retrieving NMR data: {e}")
            return {"1H": [], "13C": []}
    
    def _parse_real_nmr_data(self, soup: BeautifulSoup, compound_id: str) -> Dict:
        """Parse real NMR data from SDBS compound page."""
        nmr_data = {"1H": [], "13C": []}
        
        try:
            # Look for NMR data frames or links
            nmr_links = soup.find_all('a', href=re.compile(r'nmr|NMR'))
            
            for link in nmr_links:
                href = link.get('href', '')
                link_text = link.get_text().lower()
                
                # Check if this is a 1H or 13C NMR link
                if '1h' in link_text or 'proton' in link_text:
                    nucleus = '1H'
                elif '13c' in link_text or 'carbon' in link_text:
                    nucleus = '13C'
                else:
                    continue
                
                # Fetch the NMR spectrum page
                if href.startswith('/'):
                    nmr_url = f"https://sdbs.db.aist.go.jp{href}"
                elif href.startswith('http'):
                    nmr_url = href
                else:
                    nmr_url = f"https://sdbs.db.aist.go.jp/sdbs/cgi-bin/{href}"
                
                try:
                    self._rate_limit()
                    nmr_response = self.session.get(nmr_url, timeout=10)
                    nmr_response.raise_for_status()
                    
                    nmr_soup = BeautifulSoup(nmr_response.content, 'html.parser')
                    peaks = self._extract_peaks_from_nmr_page(nmr_soup, nucleus)
                    
                    if peaks:
                        nmr_data[nucleus] = peaks
                        
                except Exception as e:
                    print(f"Error fetching {nucleus} NMR data: {e}")
                    continue
            
            # If no NMR links found, try to parse data from the main page
            if not nmr_data["1H"] and not nmr_data["13C"]:
                # Look for NMR data directly on the compound page
                page_text = soup.get_text()
                nmr_data = self._extract_nmr_from_text(page_text)
        
        except Exception as e:
            print(f"Error parsing real NMR data: {e}")
        
        return nmr_data
    
    def _extract_peaks_from_nmr_page(self, soup: BeautifulSoup, nucleus: str) -> List[Dict]:
        """Extract peak data from an NMR spectrum page."""
        peaks = []
        
        try:
            # Look for peak assignment tables or text
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        cell_text = ' '.join(cell.get_text() for cell in cells)
                        
                        # Look for chemical shift patterns
                        if nucleus == '1H':
                            # Pattern: δ 7.25 (s, 1H) or similar
                            matches = re.findall(r'δ?\s*(\d+\.?\d*)\s*(?:ppm)?\s*\(([stdqm]+),?\s*(\d+\.?\d*)H?\)', cell_text, re.I)
                            for match in matches:
                                try:
                                    peaks.append({
                                        "shift": float(match[0]),
                                        "multiplicity": match[1].lower(),
                                        "integration": float(match[2]),
                                        "coupling": []
                                    })
                                except ValueError:
                                    continue
                        
                        elif nucleus == '13C':
                            # Pattern: δ 128.5 or similar
                            matches = re.findall(r'δ?\s*(\d+\.?\d*)\s*(?:ppm)?', cell_text)
                            for match in matches:
                                try:
                                    shift = float(match)
                                    if 0 <= shift <= 250:  # Reasonable 13C range
                                        peaks.append({
                                            "shift": shift,
                                            "multiplicity": "s",
                                            "integration": 1,
                                            "coupling": []
                                        })
                                except ValueError:
                                    continue
            
            # Also check text content for NMR assignments
            page_text = soup.get_text()
            if nucleus == '1H':
                # More flexible 1H pattern matching
                h_patterns = [
                    r'(\d+\.?\d*)\s*ppm\s*\(([stdqm]+),?\s*(\d+\.?\d*)H\)',
                    r'δ\s*(\d+\.?\d*)\s*\(([stdqm]+),?\s*(\d+\.?\d*)H\)',
                    r'(\d+\.?\d*)\s*\(([stdqm]+),?\s*(\d+\.?\d*)H\)'
                ]
                
                for pattern in h_patterns:
                    matches = re.findall(pattern, page_text, re.I)
                    for match in matches:
                        try:
                            shift = float(match[0])
                            if 0 <= shift <= 15:  # Reasonable 1H range
                                peaks.append({
                                    "shift": shift,
                                    "multiplicity": match[1].lower(),
                                    "integration": float(match[2]),
                                    "coupling": []
                                })
                        except ValueError:
                            continue
            
        except Exception as e:
            print(f"Error extracting peaks from {nucleus} NMR page: {e}")
        
        return peaks
    
    def _extract_nmr_from_text(self, text: str) -> Dict:
        """Extract NMR data from page text when no dedicated NMR pages exist."""
        nmr_data = {"1H": [], "13C": []}
        
        try:
            # Look for 1H NMR patterns in text
            h_patterns = [
                r'1H\s+NMR.*?δ\s*(\d+\.?\d*)\s*\(([stdqm]+),?\s*(\d+\.?\d*)H\)',
                r'1H\s+NMR.*?(\d+\.?\d*)\s*ppm\s*\(([stdqm]+),?\s*(\d+\.?\d*)H\)'
            ]
            
            for pattern in h_patterns:
                matches = re.findall(pattern, text, re.I | re.DOTALL)
                for match in matches:
                    try:
                        nmr_data["1H"].append({
                            "shift": float(match[0]),
                            "multiplicity": match[1].lower(),
                            "integration": float(match[2]),
                            "coupling": []
                        })
                    except ValueError:
                        continue
            
            # Look for 13C NMR patterns
            c_patterns = [
                r'13C\s+NMR.*?δ\s*(\d+\.?\d*)',
                r'13C\s+NMR.*?(\d+\.?\d*)\s*ppm'
            ]
            
            for pattern in c_patterns:
                matches = re.findall(pattern, text, re.I | re.DOTALL)
                for match in matches:
                    try:
                        shift = float(match)
                        if 0 <= shift <= 250:
                            nmr_data["13C"].append({
                                "shift": shift,
                                "multiplicity": "s",
                                "integration": 1,
                                "coupling": []
                            })
                    except ValueError:
                        continue
        
        except Exception as e:
            print(f"Error extracting NMR from text: {e}")
        
        return nmr_data
    
    def _parse_nmr_data(self, soup: BeautifulSoup) -> Dict:
        """Parse NMR data from SDBS HTML."""
        nmr_data = {"1H": [], "13C": []}
        
        # Look for NMR data sections
        # This is a simplified parser - real SDBS parsing would be more complex
        nmr_sections = soup.find_all(['div', 'table'], class_=re.compile(r'nmr|spectrum', re.I))
        
        for section in nmr_sections:
            text = section.get_text()
            
            # Look for 1H NMR data
            h_matches = re.findall(r'(\d+\.?\d*)\s*ppm.*?([stdqm])\s*.*?(\d+\.?\d*)H', text, re.I)
            for match in h_matches:
                try:
                    shift = float(match[0])
                    mult = match[1].lower()
                    integration = float(match[2])
                    
                    nmr_data["1H"].append({
                        "shift": shift,
                        "multiplicity": mult,
                        "integration": integration,
                        "coupling": []  # Coupling constants would need additional parsing
                    })
                except ValueError:
                    continue
            
            # Look for 13C NMR data
            c_matches = re.findall(r'(\d+\.?\d*)\s*ppm', text)
            for match in c_matches:
                try:
                    shift = float(match)
                    if 0 <= shift <= 250:  # Reasonable 13C range
                        nmr_data["13C"].append({
                            "shift": shift,
                            "multiplicity": "s",
                            "integration": 1
                        })
                except ValueError:
                    continue
        
        return nmr_data
    
    def test_connection(self) -> bool:
        """Test connection to SDBS website."""
        try:
            response = self.session.get(self.base_url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
