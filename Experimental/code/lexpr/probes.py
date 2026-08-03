import numpy as np

EPS = 1e-9


def correlation_clusters(F: np.ndarray, theta: float = 0.6) -> list[list[int]]:
    F = np.asarray(F, dtype=float)
    m = F.shape[1]
    if F.shape[0] < 2:
        return [[i] for i in range(m)]
    centered = F - F.mean(axis=0, keepdims=True)
    norms = np.linalg.norm(centered, axis=0)
    valid = norms > EPS
    C = np.eye(m)
    if valid.any():
        standardized = centered[:, valid] / norms[valid]
        C[np.ix_(valid, valid)] = np.clip(standardized.T @ standardized, -1.0, 1.0)
    adj = C >= theta
    seen = np.zeros(m, dtype=bool)
    clusters = []
    for i in range(m):
        if seen[i]:
            continue
        stack, comp = [i], []
        while stack:
            u = stack.pop()
            if seen[u]:
                continue
            seen[u] = True
            comp.append(u)
            stack.extend(int(v) for v in np.where(adj[u])[0] if not seen[v])
        clusters.append(sorted(comp))
    return clusters


def build_probes(
    F, theta=0.6, use_singletons=True, use_mean=True, use_max=True, use_clusters=True
):
    m = F.shape[1]
    probes, labels = [], []
    if use_singletons:
        for i in range(m):
            probes.append(lambda r, i=i: r[:, i])
            labels.append(f"f{i+1}")
    if m > 1:
        if use_mean:
            probes.append(lambda r: r.mean(axis=1))
            labels.append("mean(all)")
        if use_max:
            probes.append(lambda r: r.max(axis=1))
            labels.append("max(all)")
    clusters = correlation_clusters(F, theta) if use_clusters else []
    for c in clusters:
        if len(c) < 2:
            continue
        idx = np.array(c)
        if use_mean:
            probes.append(lambda r, idx=idx: r[:, idx].mean(axis=1))
            labels.append("mean(" + ",".join(f"f{i+1}" for i in c) + ")")
        if use_max:
            probes.append(lambda r, idx=idx: r[:, idx].max(axis=1))
            labels.append("max(" + ",".join(f"f{i+1}" for i in c) + ")")
    return probes, labels


def build_full_probes(F):
    import itertools

    m = F.shape[1]
    probes, labels = [], []
    for k in range(1, m + 1):
        for S in itertools.combinations(range(m), k):
            idx = np.array(S)
            probes.append(lambda r, idx=idx: r[:, idx].mean(axis=1))
            labels.append("mean" + str(S))
            if k > 1:
                probes.append(lambda r, idx=idx: r[:, idx].max(axis=1))
                labels.append("max" + str(S))
    return probes, labels


def build_random_probes(F, k, rng):
    m = F.shape[1]
    probes, labels = [], []
    for j in range(k):
        w = rng.dirichlet(np.ones(m))
        probes.append(lambda r, w=w: r @ w)
        labels.append(f"rand{j}")
    return probes, labels
