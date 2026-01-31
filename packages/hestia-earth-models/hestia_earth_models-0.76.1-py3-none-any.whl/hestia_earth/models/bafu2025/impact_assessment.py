from hestia_earth.models.utils.background_resourceUse import run as run_resourceUse
from .utils import LOOKUP_MAPPING_KEY, LOOKUP_NAME_PREFIX, LOOKUP_INDEX_KEY
from . import MODEL

REQUIREMENTS = {
    "ImpactAssessment": {
        "cycle": {
            "@type": "Cycle",
            "products": [
                {
                    "@type": "Product",
                    "primary": "True",
                    "value": "> 0",
                    "economicValueShare": "> 0",
                }
            ],
            "inputs": [
                {
                    "@type": "Input",
                    "value": "> 0",
                    "none": {"fromCycle": "True", "producedInCycle": "True"},
                    "term.termType": [
                        "material",
                        "fuel",
                        "soilAmendment",
                        "pesticideAI",
                        "inorganicFertiliser",
                        "electricity",
                    ],
                }
            ],
        }
    }
}
RETURNS = {
    "Indicator": [
        {
            "term": "",
            "value": "",
            "inputs": "",
            "operation": "",
        }
    ]
}
LOOKUPS = {
    "bafu2025-resourceUse": "",
    "emission": "inputProductionGroupId",
    "electricity": "bafuMapping",
    "fuel": "bafuMapping",
    "inorganicFertiliser": "bafuMapping",
    "material": "bafuMapping",
    "pesticideAI": "bafuMapping",
    "soilAmendment": "bafuMapping",
    "transport": "bafuMapping",
    "veterinaryDrugs": "bafuMapping",
    "feedFoodAdditive": "bafuMapping",
}
MODEL_KEY = "impact_assessment"


def run(impact_assessment: dict):
    return run_resourceUse(
        model=MODEL,
        impact_assessment=impact_assessment,
        lookup_mapping_key=LOOKUP_MAPPING_KEY,
        lookup_values=(LOOKUP_NAME_PREFIX, LOOKUP_INDEX_KEY),
        filter_term_types=REQUIREMENTS["ImpactAssessment"]["cycle"]["inputs"][0][
            "term.termType"
        ],
        filter_by_country=True,
    )
