# -*- coding: utf-8 -*-
"""
Created on Mon May 11 10:38:21 2026

@author: Olive
"""

import numpy as np
import torch
import librosa
from transformers import ClapModel, ClapProcessor

from .models import InstrumentMatch, ClassificationResult
from .instrument_labels import LABELS_BY_STEM
from separation.models import Stem, StemCollection

MODEL_ID = "laion/clap-htsat-unfused"   # best open-source CLAP checkpoint
CONFIDENCE_THRESHOLD = 0.28             # tuned empirically — adjust per your data
CHUNK_SECONDS = 10                      # analyse in chunks, take the max score
CHUNK_HOP_SECONDS = 5                   # 50% overlap between chunks

_model_cache = None
_processor_cache = None


def _get_model():
    global _model_cache, _processor_cache
    if _model_cache is None:
        _model_cache = ClapModel.from_pretrained(MODEL_ID)
        _processor_cache = ClapProcessor.from_pretrained(MODEL_ID)
        _model_cache.eval()
    return _model_cache, _processor_cache


def classify_stem(stem: Stem) -> ClassificationResult:
    """
    Run CLAP classification on a single stem.
    Scores the stem audio against the label list for its stem type.
    Returns a ClassificationResult with ranked matches.
    """
    model, processor = _get_model()
    labels = LABELS_BY_STEM.get(stem.name, [])

    if not labels:
        return ClassificationResult(
            stem_name=stem.name,
            matches=[],
            top_label="unknown",
            top_confidence=0.0,
            needs_user_input=True,
        )

    # Score across chunks and take the max per label
    # (a 3-minute stem may only have guitar in 30 seconds of it)
    chunk_scores = _score_chunks(stem.audio, stem.sample_rate, labels, model, processor)
    label_scores = np.max(chunk_scores, axis=0)   # (num_labels,) — best chunk per label

    # Rank labels by score
    ranked_indices = np.argsort(label_scores)[::-1]
    matches = [
        InstrumentMatch(
            label=labels[i],
            confidence=float(label_scores[i]),
            is_confident=float(label_scores[i]) >= CONFIDENCE_THRESHOLD,
        )
        for i in ranked_indices
    ]

    top = matches[0]
    return ClassificationResult(
        stem_name=stem.name,
        matches=matches,
        top_label=top.label,
        top_confidence=top.confidence,
        needs_user_input=not top.is_confident,
    )


def classify_all_stems(collection: StemCollection) -> dict[str, ClassificationResult]:
    """
    Classify every active stem in a StemCollection.
    Returns { stem_name: ClassificationResult }.
    """
    results = {}
    for name in collection.active_stems:
        stem = collection.stems[name]
        results[name] = classify_stem(stem)
    return results


def _score_chunks(
    audio: np.ndarray,
    sample_rate: int,
    labels: list[str],
    model: ClapModel,
    processor: ClapProcessor,
) -> np.ndarray:
    """
    Split audio into overlapping chunks, score each chunk against
    all labels, return array of shape (num_chunks, num_labels).
    """
    chunk_samples = int(CHUNK_SECONDS * sample_rate)
    hop_samples   = int(CHUNK_HOP_SECONDS * sample_rate)
    total_samples = len(audio)

    all_scores = []
    start = 0
    while start < total_samples:
        chunk = audio[start : start + chunk_samples]

        # Pad last chunk if shorter than chunk_samples
        if len(chunk) < chunk_samples:
            chunk = np.pad(chunk, (0, chunk_samples - len(chunk)))

        scores = _score_single_chunk(chunk, sample_rate, labels, model, processor)
        all_scores.append(scores)
        start += hop_samples

        if start + chunk_samples > total_samples and start > 0:
            break

    return np.array(all_scores)   # (num_chunks, num_labels)


def _score_single_chunk(
    chunk: np.ndarray,
    sample_rate: int,
    labels: list[str],
    model: ClapModel,
    processor: ClapProcessor,
) -> np.ndarray:
    """
    Score one audio chunk against all labels.
    Returns cosine similarity scores as a numpy array.
    """
    # CLAP expects 48kHz — resample if needed
    if sample_rate != 48000:
        chunk = librosa.resample(chunk, orig_sr=sample_rate, target_sr=48000)

    inputs = processor(
        text=labels,
        audio=[chunk],
        return_tensors="pt",
        padding=True,
        sampling_rate=48000,
    )

    with torch.no_grad():
        outputs = model(**inputs)

    # Normalised embeddings → cosine similarity via dot product
    audio_emb = outputs.audio_embeds / outputs.audio_embeds.norm(dim=-1, keepdim=True)
    text_emb  = outputs.text_embeds  / outputs.text_embeds.norm(dim=-1, keepdim=True)
    scores = (audio_emb @ text_emb.T).squeeze(0).numpy()   # (num_labels,)

    return scores