from hestia_earth.schema import EmissionMethodTier

from hestia_earth.models.utils.background_emission import run as run_emissions
from .utils import LOOKUP_MAPPING_KEY, build_lookup
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
    "emission": "inputProductionGroupId",
    "electricity": "ecoinventMapping",
    "fuel": "ecoinventMapping",
    "inorganicFertiliser": "ecoinventMapping",
    "material": "ecoinventMapping",
    "pesticideAI": "ecoinventMapping",
    "soilAmendment": "ecoinventMapping",
    "transport": "ecoinventMapping",
    "veterinaryDrugs": "ecoinventMapping",
    "feedFoodAdditive": "ecoinventMapping",
}
MODEL_KEY = "cycle"
TIER = EmissionMethodTier.BACKGROUND.value


def run(cycle: dict):
    return run_emissions(
        model=MODEL,
        cycle=cycle,
        lookup_mapping_key=LOOKUP_MAPPING_KEY,
        lookup_values=(build_lookup, None),
    )
