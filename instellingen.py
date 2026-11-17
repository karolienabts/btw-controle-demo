"""Vaste waarden voor de BTW-controle (overgenomen uit FactuurTool/instellingen.py)."""

# EU-landcodes zoals VIES ze gebruikt (Griekenland = EL, niet GR).
EU_LANDEN = [
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR",
    "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI",
    "SK", "XI",
]

VIES_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number"
VIES_TIMEOUT_SECONDEN = 20
