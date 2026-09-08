class NameSplitter:
    """Splits full names into first name and last name."""
    
    @staticmethod
    def split(full_name: str) -> tuple[str, str]:
        """
        Splits a full name.
        Example: "Martel Kingely" -> ("Martel", "Kingely")
        Example: "John" -> ("John", "")
        Example: "Sarah Jane Smith" -> ("Sarah", "Jane Smith")
        """
        if not full_name:
            return ("", "")
            
        parts = full_name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""
        
        return (first_name, last_name)
