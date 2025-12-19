"""
Analyzes server locations vs ping times to detect GeoIP mismatches

GeoIP can be inaccurate due to:
- IP registration origin vs physical location
- Multi-region datacenters (G-Portal, OVH, etc.)
- IP blocks registered in different countries
"""

# Typical ping ranges from US West Coast (in milliseconds)
# Based on geographic distance and typical routing
PING_EXPECTATIONS = {
    # North America
    "US": (10, 80),
    "CA": (20, 100),
    "MX": (30, 120),
    
    # Central/South America
    "BR": (100, 200),
    "CO": (80, 150),
    "CL": (130, 200),
    
    # Europe
    "GB": (80, 150),
    "DE": (100, 180),
    "FR": (100, 180),
    "NL": (100, 180),
    "PL": (110, 190),
    "RU": (120, 250),
    
    # Middle East
    "AE": (110, 200),
    "SA": (120, 220),
    
    # Asia
    "CN": (150, 300),
    "JP": (80, 150),
    "SG": (120, 180),
    "IN": (150, 250),
    "KR": (100, 160),
    "TH": (130, 200),
    
    # Oceania
    "AU": (150, 280),
    "NZ": (160, 290),
}


class LocationAnalyzer:
    """Analyzes ping times vs declared locations"""
    
    @staticmethod
    def get_expected_ping_range(country_code: str) -> tuple:
        """Get expected ping range for a country code"""
        return PING_EXPECTATIONS.get(country_code, (0, 1000))
    
    @staticmethod
    def is_location_mismatch(country_code: str, ping_ms: int, threshold_percent: float = 0.2) -> bool:
        """
        Detect if ping time doesn't match declared location
        
        Args:
            country_code: Two-letter country code (e.g., "DE")
            ping_ms: Measured ping in milliseconds
            threshold_percent: How far outside expected range to flag (0.2 = 20%)
        
        Returns:
            True if location seems wrong based on ping
        """
        if ping_ms is None or ping_ms <= 0 or country_code == "Unknown":
            return False
        
        min_expected, max_expected = LocationAnalyzer.get_expected_ping_range(country_code)
        
        # If ping is way lower than expected, location is probably wrong
        if ping_ms < min_expected * (1 - threshold_percent):
            return True
        
        # If ping is way higher than expected, might be wrong
        # (but give more leeway for this direction)
        if ping_ms > max_expected * (1 + threshold_percent * 2):
            return True
        
        return False
    
    @staticmethod
    def guess_likely_location(ping_ms: int) -> str:
        """
        Guess likely location based on ping time
        
        Returns country code of most likely location
        """
        if ping_ms is None or ping_ms <= 0:
            return "Unknown"
        
        # Find which region this ping matches best
        best_match = None
        best_distance = float('inf')
        
        for country, (min_ping, max_ping) in PING_EXPECTATIONS.items():
            # Calculate distance from the expected range
            if ping_ms < min_ping:
                distance = min_ping - ping_ms
            elif ping_ms > max_ping:
                distance = ping_ms - max_ping
            else:
                distance = 0
            
            if distance < best_distance:
                best_distance = distance
                best_match = country
        
        return best_match or "Unknown"
    
    @staticmethod
    def analyze_server(server_name: str, country_code: str, ping_ms: int) -> dict:
        """
        Analyze a server's location accuracy
        
        Returns dict with analysis results
        """
        is_mismatch = LocationAnalyzer.is_location_mismatch(country_code, ping_ms)
        likely_location = LocationAnalyzer.guess_likely_location(ping_ms) if is_mismatch else country_code
        expected_min, expected_max = LocationAnalyzer.get_expected_ping_range(country_code)
        
        return {
            "server_name": server_name,
            "declared_country": country_code,
            "measured_ping": ping_ms,
            "expected_ping_range": (expected_min, expected_max),
            "is_mismatch": is_mismatch,
            "likely_location": likely_location,
        }
