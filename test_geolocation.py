#!/usr/bin/env python3
"""
Test script for geolocation functionality
Tests the ipinfo.io API integration
"""

import requests

def test_geolocation():
    """Test geolocation lookup with a sample IP"""
    test_ip = '8.8.8.8'  # Google's DNS server
    
    try:
        print(f"Testing geolocation for IP: {test_ip}")
        response = requests.get(f'https://ipinfo.io/{test_ip}/json', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ Geolocation API is working!")
            print(f"  IP: {data.get('ip')}")
            print(f"  Location: {data.get('loc')}")
            print(f"  City: {data.get('city')}")
            print(f"  Region: {data.get('region')}")
            print(f"  Country: {data.get('country')}")
            print(f"  Organization: {data.get('org')}")
            
            # Parse coordinates
            loc = data.get('loc', '0,0')
            lat, lon = loc.split(',')
            print(f"\n  Coordinates:")
            print(f"    Latitude: {lat}")
            print(f"    Longitude: {lon}")
            
            return True
        else:
            print(f"\n✗ API returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error connecting to API: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Geolocation API Test")
    print("=" * 60)
    
    success = test_geolocation()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
        print("\nYou can now access the location feature at:")
        print("  http://10.60.36.1:8010/location")
    else:
        print("✗ Tests failed. Please check your internet connection.")
    print("=" * 60)
