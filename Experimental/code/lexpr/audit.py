"""Machine-readable audit certificate for a finite LexPR selection, plus an
INDEPENDENT verifier that reconstructs the winner from the exported file alone.

Three formally distinct objects (Section on auditability):
  A. labelled decision profile P(x) = ((q, D_q(x)))_q                  [interpretation]
  B. contrastive optimality record {(y, k(y), m(y))}                    [verification]
  C. complete audit record: data, bounds, probes, anchors, profiles     [reconstruction]

`verify_certificate` re-derives the winner class and the contrastive margins
using ONLY the exported record, with no access to the original objects.
"""
from __future__ import annotations
import json, hashlib
import numpy as np


def _hash(a):
    """Full SHA-256 digest of the criterion matrix, over a declared serialisation.

    The record must pin down enough for a third party to recompute the digest
    byte for byte, so the serialisation is fixed here rather than left implicit:
    C-contiguous little-endian IEEE-754 binary64, the array shape prepended as
    two 8-byte little-endian unsigned integers, negative zero normalised to
    positive zero, and NaN or infinite entries rejected outright rather than
    hashed. The digest is returned in full; a truncated digest is adequate for
    detecting accidental corruption but not for adversarial integrity, and an
    audit record should not need that distinction explained to it.
    """
    a = np.ascontiguousarray(a, dtype="<f8")
    if not np.isfinite(a).all():
        raise ValueError(
            "criterion matrix contains NaN or infinite entries; "
            "the audit record requires finite criteria"
        )
    a = a + 0.0  # normalises -0.0 to 0.0
    header = np.array(a.shape, dtype="<u8").tobytes()
    return hashlib.sha256(header + a.tobytes()).hexdigest()


def _lex_argmin_class(D):
    """Winner class under the real-valued LexPR order, evaluated on the stored
    binary64 disappointments. No quantisation: see methods.leximax_argmin."""
    S = -np.sort(-D, axis=1)
    order = np.lexsort(S.T[::-1])
    top = S[order[0]]
    winners = [int(i) for i in range(S.shape[0]) if np.array_equal(S[i], top)]
    return winners, S


def build_certificate(
    F,
    probes,
    labels,
    directions,
    ideal,
    nadir,
    candidate_ids,
    eps=1e-9,
    software_version="lexpr-1.0",
):
    """Return a JSON-serialisable complete audit record (object C) that embeds the
    labelled profiles (A) and the contrastive record (B)."""
    F = np.asarray(F, float)
    r = (F - ideal) / np.maximum(nadir - ideal, eps)
    cols, retained, removed = [], [], []
    for q, lab in zip(probes, labels):
        v = q(r)
        a, b = float(v.min()), float(v.max())
        if b - a <= eps:
            removed.append(lab)
            continue
        cols.append((v - a) / (b - a))
        retained.append((lab, a, b))
    D = np.round(np.column_stack(cols), 6)  # store and reason at export precision
    winners, S = _lex_argmin_class(D)
    profiles = {
        candidate_ids[i]: {retained[j][0]: float(D[i, j]) for j in range(D.shape[1])}
        for i in range(D.shape[0])
    }
    contrastive = None
    if len(winners) == 1:
        w = winners[0]
        sw = S[w]
        contr = []
        for y in range(D.shape[0]):
            if y == w:
                continue
            diff = np.where(sw != S[y])[0]
            k = int(diff[0]) if diff.size else len(sw)
            margin = float(S[y][k] - sw[k]) if diff.size else 0.0
            contr.append(
                {
                    "rival": candidate_ids[y],
                    "decide_coord": k + 1,
                    "margin": round(margin, 6),
                }
            )
        contrastive = contr
    return {
        "software_version": software_version,
        "candidate_ids": list(candidate_ids),
        "criterion_matrix": F.tolist(),
        "criterion_directions": list(directions),
        "criterion_hash": _hash(F),
        "ideal_bounds": list(map(float, ideal)),
        "nadir_bounds": list(map(float, nadir)),
        "declared_probes": list(labels),
        "retained_probes": [lab for lab, _, _ in retained],
        "removed_probes": removed,
        "probe_anchors": {lab: [round(a, 6), round(b, 6)] for lab, a, b in retained},
        "degeneracy_threshold": eps,
        "comparison_rule": "leximax on descending-sorted disappointments, ties to lowest id",
        "tolerance_policy": f"round to {eps} before comparison",
        "labelled_profiles": profiles,
        "winner_class": [candidate_ids[i] for i in winners],
        "contrastive_record": contrastive,
        "config_hash": None,
    }


def verify_certificate(cert):
    """Independent verifier: recompute the winner class and contrastive margins
    using ONLY the exported record. Returns (ok, messages)."""
    msgs = []
    ids = cert["candidate_ids"]
    labs = cert["retained_probes"]
    prof = cert["labelled_profiles"]
    D = np.array([[prof[c][l] for l in labs] for c in ids], float)
    eps = cert.get("degeneracy_threshold", 1e-9)
    winners, S = _lex_argmin_class(D)
    recomputed = [ids[i] for i in winners]
    ok = recomputed == cert["winner_class"]
    msgs.append(f"winner class reproduced: {ok} ({recomputed})")
    # re-hash criterion matrix
    h = _hash(np.array(cert["criterion_matrix"], float))
    hok = h == cert["criterion_hash"]
    msgs.append(f"criterion hash matches: {hok}")
    ok = ok and hok
    # re-derive contrastive margins if a unique winner
    if cert.get("contrastive_record") is not None and len(winners) == 1:
        w = winners[0]
        sw = S[w]
        good = True
        rec = {d["rival"]: d for d in cert["contrastive_record"]}
        for y in range(D.shape[0]):
            if y == w:
                continue
            diff = np.where(sw != S[y])[0]
            k = int(diff[0]) + 1 if diff.size else len(sw)
            margin = round(float(S[y][diff[0]] - sw[diff[0]]), 6) if diff.size else 0.0
            d = rec.get(ids[y])
            if d is None or d["decide_coord"] != k or abs(d["margin"] - margin) > 1e-6:
                good = False
        msgs.append(f"contrastive record reproduced: {good}")
        ok = ok and good
    return ok, msgs


def export(cert, path):
    with open(path, "w") as f:
        json.dump(cert, f, indent=2)
