#!/usr/bin/env python3
"""
Test script for enhanced GLOS Flask app routes
Run this after adding the new routes to verify functionality
"""

import requests
import json
import sys

# Base URL for your Flask app
BASE_URL = "http://localhost:5000"

def test_route(endpoint, description):
    """Test a single route and print results"""
    print(f"\n--- Testing: {description} ---")
    print(f"URL: {BASE_URL}{endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print(f"Results count: {len(data)}")
                if len(data) > 0:
                    print("Sample results:")
                    for i, item in enumerate(data[:3]):
                        print(f"  {i+1}. {item}")
            elif isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
                print(f"Sample data: {data}")
            else:
                print(f"Response: {data}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Flask app. Make sure it's running on localhost:5000")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING ENHANCED GLOS FLASK APP ROUTES")
    print("=" * 60)
    
    # Test existing routes first
    tests = [
        # Existing routes
        ("/get_atu_hierarchy", "ATU Hierarchy"),
        ("/get_types_in_range/300-399", "Tale Types in Range"),
        ("/get_type_details/300", "Tale Type Details"),
        ("/get_motifs_for_type/300", "Motifs for Tale Type"),
        
        # New reverse lookup routes
        ("/get_motif_hierarchy", "TMI Motif Hierarchy"),
        ("/get_motifs_in_category/A?limit=10", "Motifs in Category A"),
        ("/get_motif_details/A1", "Motif Details"),
        ("/get_types_for_motif/A1", "Tale Types for Motif"),
        
        # New search routes
        ("/search_motifs?q=creator&limit=5", "Search Motifs"),
        ("/search_types?q=dragon&limit=5", "Search Tale Types"),
    ]
    
    success_count = 0
    for endpoint, description in tests:
        if test_route(endpoint, description):
            success_count += 1
    
    print(f"\n" + "=" * 60)
    print(f"SUMMARY: {success_count}/{len(tests)} tests passed")
    
    if success_count == len(tests):
        print("✓ All routes working correctly!")
        print("\nNext steps:")
        print("1. Replace your existing atu_tmi.html with the enhanced version")
        print("2. Add the new routes to your app.py")
        print("3. Test the full interface at http://localhost:5000/atu_tmi")
    else:
        print("✗ Some routes failed. Check your Flask app setup.")
        
    return success_count == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
