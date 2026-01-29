from hestia_earth.schema import EmissionMethodTier

from hestia_earth.models.utils.background_emission import run as run_emissions
from .utils import LOOKUP_MAPPING_KEY, LOOKUP_NAME_PREFIX, LOOKUP_INDEX_KEY
from .utils import CUTOFF_MAX_PERCENTAGE, cutoff_value
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "inputs": [
            {
                "@type": "Input",
                "value": "> 0",
                "none": {"fromCycle": "True", "producedInCycle": "True"},
            }
        ],
        "optional": {
            "animals": [
                {
                    "@type": "Animal",
                    "inputs": [
                        {
                            "@type": "Input",
                            "value": "> 0",
                            "none": {"fromCycle": "True", "producedInCycle": "True"},
                        }
                    ],
                }
            ]
        },
    }
}
RETURNS = {
    "Emission": [
        {
            "term": "",
            "value": "",
            "methodTier": "background",
            "inputs": "",
            "operation": "",
            "animals": "",
        }
    ]
}
LOOKUPS = {
    "ecoalim-emission": "",
    "emission": "inputProductionGroupId",
    "animalProduct": "ecoalimMapping",
    "crop": "ecoalimMapping",
    "feedFoodAdditive": "ecoalimMapping",
    "forage": "ecoalimMapping",
    "processedFood": "ecoalimMapping",
}
MODEL_KEY = "cycle"
TIER = EmissionMethodTier.BACKGROUND.value


def run(cycle: dict):
    return run_emissions(
        model=MODEL,
        cycle=cycle,
        lookup_mapping_key=LOOKUP_MAPPING_KEY,
        lookup_values=(LOOKUP_NAME_PREFIX, LOOKUP_INDEX_KEY),
        cutoff_value_func=cutoff_value,
        cutoff_percentage=CUTOFF_MAX_PERCENTAGE,
    )
