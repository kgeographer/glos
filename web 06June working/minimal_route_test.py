#!/usr/bin/env python3
"""
Minimal test to verify routes are properly added to Flask app
Run this while your Flask app is running
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_basic_routes():
    """Test the most basic routes"""
    
    print("Testing basic route availability...")
    
    basic_tests = [
        "/",
        "/atu_tmi", 
        "/get_atu_hierarchy"
    ]
    
    for route in basic_tests:
        try:
            response = requests.get(f"{BASE_URL}{route}")
            print(f"✓ {route:<20} Status: {response.status_code}")
        except Exception as e:
            print(f"✗ {route:<20} Error: {e}")

def check_flask_routes():
    """Check what routes Flask actually has registered"""
    
    # This won't work from outside, but you can add this to your Flask app temporarily
    flask_debug_code = '''
# Add this temporarily to your app.py to see all registered routes:

@app.route('/debug/routes')
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
    return jsonify(routes)
'''
    
    print("\nTo debug route registration, add this to your app.py:")
    print(flask_debug_code)
    
    # Test if debug route exists
    try:
        response = requests.get(f"{BASE_URL}/debug/routes")
        if response.status_code == 200:
            routes = response.json()
            print(f"\nRegistered routes ({len(routes)}):")
            for route in routes:
                if 'atu' in route['rule'] or 'motif' in route['rule'] or 'search' in route['rule']:
                    print(f"  {route['rule']:<30} {route['methods']}")
        else:
            print(f"Debug route not available (status: {response.status_code})")
    except:
        print("Debug route not yet added to Flask app")

if __name__ == "__main__":
    test_basic_routes()
    check_flask_routes()
