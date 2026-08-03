import sys
import os
import numpy as np
import pandas as pd

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lexpr import problems, methods


def main():
    rng = np.random.default_rng(42)
    F = problems.sample_front("cars", 0, 0, rng)
    m = F.shape[1]

    # Run LexPR
    idx, D, labels, probes = methods.lexpr(F, return_detail=True)

    # Calculate SMAA acceptability indices
    n_weights = 10000
    W = rng.dirichlet(np.ones(m), size=n_weights)
    C = methods.normalize(F) @ W.T
    winners = np.argmin(C, axis=0)
    counts = np.bincount(winners, minlength=F.shape[0])
    smaa_acc = counts / n_weights

    records = []
    for i in range(F.shape[0]):
        # binding probe is the max disappointment
        binding_idx = np.argmax(D[i])
        binding_probe_label = labels[binding_idx]
        binding_disappointment = D[i, binding_idx]
        records.append(
            {
                "Alternative": i,
                "SMAA_Acceptability": smaa_acc[i],
                "LexPR_Max_Disappointment": binding_disappointment,
                "LexPR_Binding_Probe": binding_probe_label,
                "LexPR_Winner": "YES" if i == idx else "NO",
            }
        )
    df = pd.DataFrame(records)

    out_dir = "../results/protocol/current/tables"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "auditability_map.csv")
    df.to_csv(out_path, index=False)
    print(f"Auditability Map generated at {out_path}.")


if __name__ == "__main__":
    main()
