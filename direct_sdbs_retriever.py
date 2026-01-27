#!/usr/bin/env python3
"""
Direct SDBS Data Retrieval

Extracts NMR data directly from SDBS compound and spectral view pages.
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Tuple, Optional
import json


class DirectSDBSRetriever:
    """
    Direct retrieval of NMR data from SDBS compound and spectral pages.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.base_url = "https://sdbs.db.aist.go.jp"
        self.authenticated = False
        
    def _authenticate_session(self):
        """Authenticate session by accepting SDBS disclaimer."""
        if self.authenticated:
            return True
            
        try:
            print("Authenticating SDBS session...")
            disclaimer_url = f"{self.base_url}/sdbs/cgi-bin/cre_index.cgi"
            
            # Get main page
            response = self.session.get(disclaimer_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for disclaimer accept button
            disclaimer_button = soup.find('input', {'name': re.compile(r'DisclaimeraAccept')})
            
            if disclaimer_button:
                print("Accepting SDBS disclaimer...")
                
                # Extract form data
                form_data = {}
                for hidden_input in soup.find_all('input', {'type': 'hidden'}):
                    name = hidden_input.get('name')
                    value = hidden_input.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Add disclaimer acceptance
                form_data[disclaimer_button.get('name')] = disclaimer_button.get('value', 'Accept')
                form_data['__EVENTTARGET'] = ''
                form_data['__EVENTARGUMENT'] = ''
                
                # Submit disclaimer
                response = self.session.post(disclaimer_url, data=form_data, timeout=15)
                response.raise_for_status()
                
                self.authenticated = True
                print("SDBS session authenticated successfully")
                return True
            
            else:
                print("No disclaimer found, assuming session is valid")
                self.authenticated = True
                return True
                
        except Exception as e:
            print(f"Error authenticating SDBS session: {e}")
            return False
        
    def get_compound_data(self, sdbsno: str) -> Dict:
        """
        Get compound data from SDBS compound view page.
        
        Args:
            sdbsno: SDBS number (e.g., "1839")
        
        Returns:
            Dictionary with compound information and NMR data
        """
        # Authenticate session first
        if not self._authenticate_session():
            print("Failed to authenticate SDBS session")
            return {}
        
        compound_url = f"{self.base_url}/CompoundView.aspx?sdbsno={sdbsno}"
        
        try:
            print(f"Retrieving compound data for SDBS #{sdbsno}...")
            time.sleep(1)  # Rate limiting
            response = self.session.get(compound_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we got another disclaimer page
            if "Disclaimer.aspx" in response.url or soup.find('input', {'name': re.compile(r'DisclaimeraAccept')}):
                print(f"Got disclaimer page for compound {sdbsno}, accepting...")
                
                # Accept the compound-specific disclaimer
                disclaimer_button = soup.find('input', {'name': re.compile(r'DisclaimeraAccept')})
                if disclaimer_button:
                    form_data = {}
                    for hidden_input in soup.find_all('input', {'type': 'hidden'}):
                        name = hidden_input.get('name')
                        value = hidden_input.get('value', '')
                        if name:
                            form_data[name] = value
                    
                    form_data[disclaimer_button.get('name')] = disclaimer_button.get('value', 'Accept')
                    form_data['__EVENTTARGET'] = ''
                    form_data['__EVENTARGUMENT'] = ''
                    
                    # Submit the compound disclaimer
                    time.sleep(1)
                    response = self.session.post(response.url, data=form_data, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save the compound page for debugging
            with open(f'sdbs_compound_{sdbsno}.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"Saved compound page to sdbs_compound_{sdbsno}.html")
            
            # Extract basic compound information
            compound_data = self._extract_compound_info(soup, sdbsno)
            
            # Get 1H NMR data
            h1_data = self.get_h1_nmr_data(sdbsno)
            if h1_data:
                compound_data['h1_nmr'] = h1_data
            
            # Get 13C NMR data  
            c13_data = self.get_c13_nmr_data(sdbsno)
            if c13_data:
                compound_data['c13_nmr'] = c13_data
            
            return compound_data
            
        except Exception as e:
            print(f"Error retrieving compound data: {e}")
            return {}
    
    def _extract_compound_info(self, soup: BeautifulSoup, sdbsno: str) -> Dict:
        """Extract basic compound information from compound view page."""
        compound_data = {
            'sdbsno': sdbsno,
            'name': 'Unknown',
            'formula': 'Unknown',
            'molecular_weight': 0,
            'cas_number': '',
            'url': f"{self.base_url}/CompoundView.aspx?sdbsno={sdbsno}"
        }
        
        try:
            # Look for compound name in title or specific elements
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                # Extract compound name from title
                name_match = re.search(r'SDBS\s*-\s*(.+?)(?:\s*-|$)', title_text)
                if name_match:
                    compound_data['name'] = name_match.group(1).strip()
            
            # Look for molecular formula and weight in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        if 'formula' in label or 'molecular' in label:
                            if re.match(r'^[A-Z][a-z]?\d*([A-Z][a-z]?\d*)*$', value):
                                compound_data['formula'] = value
                        
                        elif 'weight' in label or 'mass' in label:
                            weight_match = re.search(r'(\d+\.?\d*)', value)
                            if weight_match:
                                compound_data['molecular_weight'] = float(weight_match.group(1))
                        
                        elif 'cas' in label:
                            compound_data['cas_number'] = value
            
            print(f"Extracted compound info: {compound_data['name']} ({compound_data['formula']})")
            return compound_data
            
        except Exception as e:
            print(f"Error extracting compound info: {e}")
            return compound_data
    
    def get_h1_nmr_data(self, sdbsno: str) -> Optional[Dict]:
        """
        Get 1H NMR data from SDBS spectral view page.
        
        Args:
            sdbsno: SDBS number
            
        Returns:
            Dictionary with 1H NMR peak data
        """
        h1_url = f"{self.base_url}/HNmrSpectralView.aspx?sdbsno={sdbsno}"
        
        try:
            print(f"Retrieving 1H NMR data for SDBS #{sdbsno}...")
            time.sleep(1)  # Rate limiting
            response = self.session.get(h1_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save the H1 page for debugging
            with open(f'sdbs_h1_{sdbsno}.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"Saved 1H NMR page to sdbs_h1_{sdbsno}.html")
            
            # Extract peak data from the page
            nmr_data = {
                'nucleus': '1H',
                'solvent': 'Unknown',
                'frequency': 'Unknown',
                'peaks': [],
                'url': h1_url
            }
            
            # Look for NMR parameters in tables or text
            self._extract_nmr_parameters(soup, nmr_data)
            
            # Extract peak data
            peaks = self._extract_h1_peaks(soup)
            nmr_data['peaks'] = peaks
            
            print(f"Found {len(peaks)} 1H NMR peaks")
            return nmr_data if peaks else None
            
        except Exception as e:
            print(f"Error retrieving 1H NMR data: {e}")
            return None
    
    def get_c13_nmr_data(self, sdbsno: str) -> Optional[Dict]:
        """
        Get 13C NMR data from SDBS spectral view page.
        
        Args:
            sdbsno: SDBS number
            
        Returns:
            Dictionary with 13C NMR peak data
        """
        c13_url = f"{self.base_url}/CNmrSpectralView.aspx?sdbsno={sdbsno}"
        
        try:
            print(f"Retrieving 13C NMR data for SDBS #{sdbsno}...")
            time.sleep(1)  # Rate limiting
            response = self.session.get(c13_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save the C13 page for debugging
            with open(f'sdbs_c13_{sdbsno}.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"Saved 13C NMR page to sdbs_c13_{sdbsno}.html")
            
            # Extract peak data from the page
            nmr_data = {
                'nucleus': '13C',
                'solvent': 'Unknown',
                'frequency': 'Unknown', 
                'peaks': [],
                'url': c13_url
            }
            
            # Look for NMR parameters
            self._extract_nmr_parameters(soup, nmr_data)
            
            # Extract peak data (13C is simpler - no multiplicity)
            peaks = self._extract_c13_peaks(soup)
            nmr_data['peaks'] = peaks
            
            print(f"Found {len(peaks)} 13C NMR peaks")
            return nmr_data if peaks else None
            
        except Exception as e:
            print(f"Error retrieving 13C NMR data: {e}")
            return None
    
    def _extract_nmr_parameters(self, soup: BeautifulSoup, nmr_data: Dict):
        """Extract NMR measurement parameters from the page."""
        text_content = soup.get_text()
        
        # Look for solvent information
        solvent_patterns = [
            r'CDCl3?', r'DMSO-d6', r'D2O', r'CD3OD', r'C6D6', r'CD3CN'
        ]
        for pattern in solvent_patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                nmr_data['solvent'] = pattern.replace('?', '')
                break
        
        # Look for frequency information
        freq_match = re.search(r'(\d+)\s*MHz', text_content)
        if freq_match:
            nmr_data['frequency'] = f"{freq_match.group(1)} MHz"
    
    def _extract_h1_peaks(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract 1H NMR peak data from the page."""
        peaks = []
        
        # Look for peak data in various formats
        text_content = soup.get_text()
        
        # Pattern for chemical shifts (common formats)
        # Examples: δ 7.25 (m, 5H), 3.85 (s, 3H), etc.
        peak_patterns = [
            r'δ?\s*(\d+\.?\d*)\s*\(([^,]+),?\s*(\d*H?)\)',
            r'(\d+\.?\d*)\s*ppm\s*\(([^,]+),?\s*(\d*H?)\)',
            r'(\d+\.?\d*)\s*\(([sdtqm]+),?\s*(\d*H?)\)'
        ]
        
        for pattern in peak_patterns:
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                try:
                    shift = float(match.group(1))
                    multiplicity = match.group(2).strip()
                    integration = match.group(3) if match.group(3) else '1H'
                    
                    # Clean up multiplicity
                    mult_clean = self._clean_multiplicity(multiplicity)
                    
                    # Extract integration number
                    int_match = re.search(r'(\d+)', integration)
                    int_value = int(int_match.group(1)) if int_match else 1
                    
                    peaks.append({
                        'shift': shift,
                        'multiplicity': mult_clean,
                        'integration': int_value,
                        'coupling': []  # Coupling constants would need additional parsing
                    })
                except (ValueError, IndexError):
                    continue
        
        # Remove duplicates and sort by chemical shift
        unique_peaks = []
        seen_shifts = set()
        for peak in peaks:
            shift_key = round(peak['shift'], 2)
            if shift_key not in seen_shifts:
                seen_shifts.add(shift_key)
                unique_peaks.append(peak)
        
        return sorted(unique_peaks, key=lambda x: x['shift'], reverse=True)
    
    def _extract_c13_peaks(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract 13C NMR peak data from the page."""
        peaks = []
        
        text_content = soup.get_text()
        
        # 13C peaks are usually just chemical shifts
        # Look for patterns like: δ 165.3, 138.2, 129.1, etc.
        shift_patterns = [
            r'δ?\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*ppm'
        ]
        
        for pattern in shift_patterns:
            matches = re.finditer(pattern, text_content)
            for match in matches:
                try:
                    shift = float(match.group(1))
                    # Filter reasonable 13C range (0-220 ppm)
                    if 0 <= shift <= 220:
                        peaks.append({
                            'shift': shift,
                            'multiplicity': 's',  # 13C is typically singlets
                            'integration': 1,
                            'coupling': []
                        })
                except ValueError:
                    continue
        
        # Remove duplicates and sort
        unique_peaks = []
        seen_shifts = set()
        for peak in peaks:
            shift_key = round(peak['shift'], 1)
            if shift_key not in seen_shifts:
                seen_shifts.add(shift_key)
                unique_peaks.append(peak)
        
        return sorted(unique_peaks, key=lambda x: x['shift'], reverse=True)
    
    def _clean_multiplicity(self, mult: str) -> str:
        """Clean and standardize multiplicity notation."""
        mult = mult.lower().strip()
        
        # Map common multiplicity patterns
        mult_map = {
            's': 's', 'singlet': 's',
            'd': 'd', 'doublet': 'd', 
            't': 't', 'triplet': 't',
            'q': 'q', 'quartet': 'q',
            'm': 'm', 'multiplet': 'm', 'multi': 'm',
            'dd': 'dd', 'dt': 'dt', 'dq': 'dq',
            'tt': 'tt', 'td': 'td'
        }
        
        for pattern, standard in mult_map.items():
            if pattern in mult:
                return standard
        
        return 'm'  # Default to multiplet


def test_direct_retrieval():
    """Test the direct SDBS retrieval system."""
    retriever = DirectSDBSRetriever()
    
    # Test with the compound you mentioned (SDBS #1839)
    test_sdbsno = "1839"
    
    print(f"=== Testing Direct SDBS Retrieval for #{test_sdbsno} ===\n")
    
    compound_data = retriever.get_compound_data(test_sdbsno)
    
    if compound_data:
        print(f"Compound: {compound_data.get('name', 'Unknown')}")
        print(f"Formula: {compound_data.get('formula', 'Unknown')}")
        print(f"MW: {compound_data.get('molecular_weight', 0)}")
        print(f"URL: {compound_data.get('url', '')}")
        
        if 'h1_nmr' in compound_data:
            h1_data = compound_data['h1_nmr']
            print(f"\n1H NMR ({h1_data.get('solvent', 'Unknown')}, {h1_data.get('frequency', 'Unknown')}):")
            for peak in h1_data.get('peaks', []):
                print(f"  δ {peak['shift']:.2f} ({peak['multiplicity']}, {peak['integration']}H)")
        
        if 'c13_nmr' in compound_data:
            c13_data = compound_data['c13_nmr']
            print(f"\n13C NMR ({c13_data.get('solvent', 'Unknown')}, {c13_data.get('frequency', 'Unknown')}):")
            for peak in c13_data.get('peaks', []):
                print(f"  δ {peak['shift']:.1f}")
        
        # Save data to file
        with open(f'sdbs_{test_sdbsno}_data.json', 'w') as f:
            json.dump(compound_data, f, indent=2)
        print(f"\nData saved to sdbs_{test_sdbsno}_data.json")
    
    else:
        print("Failed to retrieve compound data")


if __name__ == "__main__":
    test_direct_retrieval()
