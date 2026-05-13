# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:48:22 2026

@author: Olive
"""

from classification.models import ClassificationResult
from separation.models import StemCollection
from .models import (
    UserSelectionRequest,
    UserSelectionResponse,
    StemSelection,
    OutputChoice,
)

TOP_N_FOR_UNCLEAR = 3   # how many label options to show for unclear stems


def build_selection_request(
    classifications: dict[str, ClassificationResult],
    collection: StemCollection,
) -> UserSelectionRequest:
    """
    Build the payload the frontend needs to render the instrument
    selection UI. Separates confident hits from unclear ones.
    """
    confirmed = []
    unclear   = []

    for stem_name, result in classifications.items():
        if not result.needs_user_input:
            confirmed.append({
                "stem":       stem_name,
                "label":      result.top_label,
                "confidence": round(result.top_confidence * 100),
            })
        else:
            # Give user the top N candidates to choose from
            top3 = [
                {"label": m.label, "confidence": round(m.confidence * 100)}
                for m in result.matches[:TOP_N_FOR_UNCLEAR]
            ]
            unclear.append({
                "stem":     stem_name,
                "top3":     top3,
            })

    return UserSelectionRequest(
        confirmed_instruments=confirmed,
        unclear_stems=unclear,
        track_metadata=collection.source_metadata,
    )


def process_user_response(
    response: UserSelectionResponse,
    classifications: dict[str, ClassificationResult],
) -> list[StemSelection]:
    """
    Validate and normalise the user's selections.
    Returns a clean list of StemSelections ready for the output layer.
    """
    valid_stems = set(classifications.keys())
    validated = []

    for sel in response.selections:
        if sel.stem_name not in valid_stems:
            raise ValueError(f"Unknown stem in selection: '{sel.stem_name}'")
        if not sel.instrument_label:
            raise ValueError(f"No instrument label for stem: '{sel.stem_name}'")
        validated.append(sel)

    if not validated:
        raise ValueError("No instruments selected. Please choose at least one.")

    return validated