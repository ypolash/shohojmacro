class CountryMapper:
    """Maps between full country names, ISO codes, and proxy session identifiers."""
    
    # Mapping based on common proxy ISO codes and NBA form names
    _MAP = {
        "United Kingdom": {"iso": "GB", "proxy_code": "gb", "phone_code": "+44"},
        "United States": {"iso": "US", "proxy_code": "us", "phone_code": "+1"},
        "Canada": {"iso": "CA", "proxy_code": "ca", "phone_code": "+1"},
        "Germany": {"iso": "DE", "proxy_code": "de", "phone_code": "+49"},
        "France": {"iso": "FR", "proxy_code": "fr", "phone_code": "+33"},
        "Australia": {"iso": "AU", "proxy_code": "au", "phone_code": "+61"},
        # Add more as needed
    }
    
    @classmethod
    def get_proxy_code(cls, country_name: str) -> str:
        """'United Kingdom' -> 'gb'"""
        data = cls._MAP.get(country_name)
        if data:
            return data["proxy_code"]
        # Fallback: try lowercase first two letters
        return country_name[:2].lower()
        
    @classmethod
    def get_iso_code(cls, country_name: str) -> str:
        """'United Kingdom' -> 'GB'"""
        data = cls._MAP.get(country_name)
        if data:
            return data["iso"]
        return country_name[:2].upper()
        
    @classmethod
    def get_phone_code(cls, country_name: str) -> str:
        """'United Kingdom' -> '+44'"""
        data = cls._MAP.get(country_name)
        return data["phone_code"] if data else ""
        
    @classmethod
    def get_session_filename(cls, country_name: str) -> str:
        """'United Kingdom' -> 'session_gb.txt'"""
        code = cls.get_proxy_code(country_name)
        return f"session_{code}.txt"
