# getfactormodels/registry.py
from types import MappingProxyType
from getfactormodels.models.base import FactorModel
from getfactormodels.models.fama_french import FamaFrenchFactors, FFIndustryPortfolios
from getfactormodels.models.carhart import CarhartFactors
from getfactormodels.models.q_factors import QFactors
from getfactormodels.models import *

# Maps canonical keys to lists of user-friendly variations
_MODEL_ALIASES = {
    # Factors
    "3": ["3", "ff3", "famafrench3"],
    "4": ["4", "ff4", "carhart", "car"],
    "5": ["5", "ff5", "famafrench5"],
    "6": ["6", "ff6", "famafrench6"],
    "Q": ["q", "qfactors", "q-factors", "q_factors", "q5", "hmxz"],
    "Qclassic": ["q4", "qclassic", "q-classic", "q_classic", "classic_q"],
    "HMLDevil": ["hmld", "hmldevil", "hml_devil", "devil"],
    "QMJ": ["qmj", "quality", "qualityminusjunk"],
    "BAB": ["bab", "betting", "bettingainstbeta"],
    "Mispricing": ["mispricing", "mis", "misp"],
    "Liquidity": ["liq", "liquidity"],
    "ICR": ["icr", "intermediary", "hkm"],
    "DHS": ["dhs", "behavioural", "behaviour"],
    "BarillasShanken": ["bs", "bs6", "barillasshanken", "barillas-shanken"],
    "VME": ["vme", "valmom", "valueandmomentumeverywhere"],
    "AQR6": ["aqr6", "aqr", "aqrfactors"],
    "HighIncomeCCAPM": ["hccapm", 'hcapm', 'hc-capm'],
    "ConditionalCAPM": ["jwcapm", "plcapm", "jwccapm", "plccapm", "ccapm"],
    # FF Portfolios
    "Industry": ["industry", "ind", "sector"],
}

# Invert aliases for O(1) lookup: 'ff3' -> '3'
_ALIAS_LOOKUP = {
    alias: key 
    for key, aliases in _MODEL_ALIASES.items() 
    for alias in aliases
}

# map key to the class
_CLASS_REGISTRY = {
    "3": FamaFrenchFactors,
    "4": CarhartFactors,
    "5": FamaFrenchFactors,
    "6": FamaFrenchFactors,
    "Q": QFactors,
    "Qclassic": QFactors,
    "Industry": FFIndustryPortfolios,
}

def resolve_model_key(user_input: str | int) -> str:
    """
    Normalize user input to a canonical key.
    Example: 'ff3' -> '3', 'industry' -> 'Industry'
    """
    if not user_input:
        raise ValueError("Model name cannot be empty.")
        
    val = str(user_input).lower().strip().replace("-", "").replace("_", "")
    
    # Direct match or alias match
    if val in _ALIAS_LOOKUP:
        return _ALIAS_LOOKUP[val]
        
    # Fallback: if the user passes "3" (int) or strict key
    for key in _CLASS_REGISTRY:
        if val == key.lower():
            return key
            
    raise ValueError(f"Unknown model or portfolio: '{user_input}'")

def get_model_class(key: str) -> "FactorModel":
    """Retrieve the class constructor for a resolved key."""
    if key not in _CLASS_REGISTRY:
        raise ValueError(f"Model key '{key}' is valid but not registered to a class.")
    return _CLASS_REGISTRY[key]
