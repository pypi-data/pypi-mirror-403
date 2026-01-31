from hestia_earth.schema import EmissionMethodTier

from hestia_earth.models.utils.background_emission import run as run_emissions
from .utils import LOOKUP_MAPPING_KEY, LOOKUP_NAME_PREFIX, LOOKUP_INDEX_KEY
from . import MODEL

REQUIREMENTS = {
    "Cycle": {
        "inputs": [
            {
                "@type": "Input",
                "value": "> 0",
                "none": {"fromCycle": "True", "producedInCycle": "True"},
                "term.termType": ["material"],
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
                            "term.termType": ["material"],
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
    "worldsteel-emission": "",
    "emission": "inputProductionGroupId",
    "material": "worldsteelMapping",
}
MODEL_KEY = "cycle"
TIER = EmissionMethodTier.BACKGROUND.value


def run(cycle: dict):
    return run_emissions(
        model=MODEL,
        cycle=cycle,
        lookup_mapping_key=LOOKUP_MAPPING_KEY,
        lookup_values=(LOOKUP_NAME_PREFIX, LOOKUP_INDEX_KEY),
        filter_term_types=REQUIREMENTS["Cycle"]["inputs"][0]["term.termType"],
    )
