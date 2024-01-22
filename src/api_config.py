from dataclasses import dataclass

@dataclass
class ConfigRegister:
    """ Store API secrets here."""
    api_id: int = 12345678
    api_hash: str = "hash123"
