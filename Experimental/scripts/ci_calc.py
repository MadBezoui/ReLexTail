import pandas as pd
import numpy as np
import scipy.stats as st

df = pd.read_csv('../manuscript/generated/tables/benchmark_raw.csv')
for metric in ['mean', 'tail_mean']:
    print(f"\n--- {metric} ---")
    pivot = df.pivot(index=['dataset', 'rep'], columns='method', values=metric)
    for m in ['Leximax', 'LexPR', 'ReLexTail_0.01']:
        mean_val = pivot[m].mean()
        print(f"{m}: mean={mean_val:.4f}")
        if m != 'LexPR':
            diff = pivot[m] - pivot['LexPR']
            ci = st.t.interval(0.95, len(diff)-1, loc=np.mean(diff), scale=st.sem(diff))
            print(f"  Paired diff vs LexPR: {diff.mean():.4f} CI: [{ci[0]:.4f}, {ci[1]:.4f}]")
