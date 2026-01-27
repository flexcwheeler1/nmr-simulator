#!/usr/bin/env python3
"""
Debug script to understand SDBS website structure and improve parsing.
"""

import requests
from bs4 import BeautifulSoup
import re
import time

def debug_sdbs_structure():
    """Debug the SDBS website structure to understand how to parse it correctly."""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    print("=== SDBS Debug Analysis ===\n")
    
    # Step 1: Check main page
    print("1. Checking main SDBS page...")
    try:
        main_url = "https://sdbs.db.aist.go.jp/sdbs/cgi-bin/cre_index.cgi"
        response = session.get(main_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"   Status: {response.status_code}")
        print(f"   Title: {soup.title.get_text() if soup.title else 'No title'}")
        print(f"   Content length: {len(response.text)} characters")
        
        # Check for forms
        forms = soup.find_all('form')
        print(f"   Found {len(forms)} forms")
        
        for i, form in enumerate(forms):
            action = form.get('action', 'No action')
            method = form.get('method', 'GET')
            print(f"     Form {i+1}: {method} -> {action}")
            
            inputs = form.find_all(['input', 'select', 'textarea'])
            for inp in inputs:
                name = inp.get('name', 'no-name')
                inp_type = inp.get('type', inp.name)
                print(f"       Input: {name} ({inp_type})")
        
        # Check for disclaimer/agreement content
        text_content = soup.get_text().lower()
        if 'disclaimer' in text_content or 'agree' in text_content:
            print("   ⚠️  Disclaimer/agreement content detected")
        else:
            print("   ✅ No disclaimer detected")
        
    except Exception as e:
        print(f"   ❌ Error accessing main page: {e}")
        return
    
    # Step 2: Try different search approaches
    print("\n2. Testing search approaches...")
    
    search_terms = ["indole", "benzene", "ethanol"]
    
    for term in search_terms:
        print(f"\n   Searching for: {term}")
        
        # Try different search URLs and parameters
        search_configs = [
            {
                'url': 'https://sdbs.db.aist.go.jp/sdbs/cgi-bin/cre_index.cgi',
                'params': {'compound': term, 'lang': 'eng'},
                'method': 'GET'
            },
            {
                'url': 'https://sdbs.db.aist.go.jp/sdbs/cgi-bin/direct_frame_disp.cgi',
                'params': {'compound': term},
                'method': 'GET'
            },
            {
                'url': 'https://sdbs.db.aist.go.jp/sdbs/cgi-bin/cre_index.cgi',
                'params': {'compound': term, 'lang': 'eng'},
                'method': 'POST'
            }
        ]
        
        for config in search_configs:
            try:
                time.sleep(1)  # Rate limiting
                
                if config['method'] == 'GET':
                    response = session.get(config['url'], params=config['params'], timeout=15)
                else:
                    response = session.post(config['url'], data=config['params'], timeout=15)
                
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                print(f"     {config['method']} {config['url']}")
                print(f"     Status: {response.status_code}, Length: {len(response.text)}")
                
                # Look for SDBS-specific patterns
                sdbs_links = soup.find_all('a', href=re.compile(r'sdbsno='))
                print(f"     SDBS links found: {len(sdbs_links)}")
                
                if sdbs_links:
                    for link in sdbs_links[:3]:  # Show first 3
                        href = link.get('href', '')
                        text = link.get_text(strip=True)
                        print(f"       → {text}: {href}")
                
                # Look for compound tables
                tables = soup.find_all('table')
                print(f"     Tables found: {len(tables)}")
                
                # Look for result indicators
                text_lower = soup.get_text().lower()
                result_indicators = ['results', 'compounds', 'found', 'matches']
                found_indicators = [ind for ind in result_indicators if ind in text_lower]
                if found_indicators:
                    print(f"     Result indicators: {', '.join(found_indicators)}")
                
                # Check for error messages
                error_indicators = ['error', 'not found', 'no results', 'invalid']
                found_errors = [err for err in error_indicators if err in text_lower]
                if found_errors:
                    print(f"     ⚠️  Error indicators: {', '.join(found_errors)}")
                
                # Save a sample of the HTML for inspection
                if len(sdbs_links) > 0:
                    sample_file = f"sdbs_sample_{term}_{config['method'].lower()}.html"
                    with open(sample_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"     💾 Saved sample HTML to {sample_file}")
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
    
    print("\n=== Debug Complete ===")
    print("Check the saved HTML files to understand the actual structure.")

if __name__ == "__main__":
    debug_sdbs_structure()
