#!/usr/bin/env python3
"""
Demo script for the geolocation feature
Shows example API responses for different IPs
"""

import requests
from datetime import datetime

def demo_location(ip, description):
    """Demo geolocation for a specific IP"""
    print(f"\n{'=' * 70}")
    print(f"Testing: {description}")
    print(f"IP Address: {ip}")
    print('=' * 70)
    
    try:
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse coordinates
            loc = data.get('loc', '0,0')
            lat, lon = loc.split(',')
            
            print(f"\n✓ Location found!")
            print(f"  📍 City:        {data.get('city', 'Unknown')}")
            print(f"  🗺️  Region:      {data.get('region', 'Unknown')}")
            print(f"  🌍 Country:     {data.get('country', 'Unknown')}")
            print(f"  📊 Coordinates: {lat}, {lon}")
            print(f"  🏢 ISP/Org:     {data.get('org', 'Unknown')}")
            print(f"\n  Map URL: http://10.60.36.1:8010/location")
            print(f"  (When accessing from this IP, you'll see it on the map)")
            
        else:
            print(f"\n✗ API returned status code: {response.status_code}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")

def main():
    """Run demo for multiple sample IPs"""
    print("\n" + "=" * 70)
    print(" " * 15 + "GEOLOCATION FEATURE DEMO")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Demo various IPs from different locations
    test_cases = [
        ("8.8.8.8", "Google DNS (Mountain View, California)"),
        ("1.1.1.1", "Cloudflare DNS (may show various locations)"),
        ("208.67.222.222", "OpenDNS (San Francisco, California)"),
    ]
    
    for ip, desc in test_cases:
        demo_location(ip, desc)
    
    print("\n" + "=" * 70)
    print("\n🎉 Demo Complete!")
    print("\nTo see your own location:")
    print("  1. Visit: http://10.60.36.1:8010/location")
    print("  2. The page will automatically detect your IP")
    print("  3. Your location will be shown on an interactive map")
    print("\nFeatures:")
    print("  ✓ Automatic IP detection")
    print("  ✓ Interactive Leaflet map with OpenStreetMap")
    print("  ✓ Marker with popup showing location details")
    print("  ✓ Zoom and pan controls")
    print("  ✓ Responsive design")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
