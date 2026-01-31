import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
import numpy as np
import pandas as pd
from sklearn.metrics import homogeneity_completeness_v_measure, adjusted_rand_score, normalized_mutual_info_score


def _safe_div(a, b):
    return a / b if b else 0.0

def compute_cluster_cohesion(y_true, y_pred, noise_labels=(-1, None, np.nan)):
    """
    Evaluate 'did points from each TRUE cluster map to a SINGLE predicted cluster?'
    Returns:
      metrics: dict of global scores (focus on 'completeness' and 'b3_recall')
      per_true_cluster: DataFrame with fragmentation stats per true cluster
    """
    y_true = pd.Series(y_true).reset_index(drop=True)
    y_pred = pd.Series(y_pred).reset_index(drop=True)

    # Handle NaNs & optional noise labels in predictions
    pred_clean = y_pred.copy()
    pred_clean = pred_clean.where(~pred_clean.isin(noise_labels), other=np.nan)

    # Filter rows where both labels exist
    mask = (~y_true.isna()) & (~pred_clean.isna())
    yt = y_true[mask].to_numpy()
    yp = pred_clean[mask].to_numpy()

    # ---- Global reference metrics
    h, c, v = homogeneity_completeness_v_measure(yt, yp)
    ari = adjusted_rand_score(yt, yp)
    nmi = normalized_mutual_info_score(yt, yp)

    # ---- B³ recall (completeness-like)
    # For each sample, recall = (# items in its TRUE cluster that share its PRED label) / (size of its TRUE cluster)
    df = pd.DataFrame({"yt": yt, "yp": yp})
    true_sizes = df.groupby("yt").size().rename("n_true")
    joint_sizes = df.groupby(["yt", "yp"]).size().rename("n_joint").reset_index()
    df = df.merge(true_sizes, left_on="yt", right_index=True, how="left")
    df = df.merge(joint_sizes, on=["yt","yp"], how="left")
    b3_recall_per_point = (df["n_joint"] / df["n_true"]).to_numpy()
    b3_recall = float(b3_recall_per_point.mean())

    # ---- Per-true-cluster fragmentation stats
    per_true = []
    for g, sub in pd.DataFrame({"yt": yt, "yp": yp}).groupby("yt"):
        counts = sub["yp"].value_counts()
        n = counts.sum()
        max_share = counts.max() / n                       # majority capture
        n_pred_used = counts.size                          # how many predicted clusters used
        p = (counts / n).to_numpy(float)
        entropy = -np.sum(p * np.log2(p + 1e-12))         # cluster-level mixing
        # B³ recall for this true cluster is the same as majority capture only if all points share one pred label;
        # compute exact mean of per-point B³ recall within this cluster:
        b3_rec_cluster = np.mean((counts / n).reindex(sub["yp"]).to_numpy())
        per_true.append({
            "true_cluster": g,
            "n_points": int(n),
            "majority_capture": float(max_share),          # 1.0 = perfect (no splitting)
            "pred_clusters_used": int(n_pred_used),
            "pred_label_entropy_bits": float(entropy),
            "b3_recall_cluster": float(b3_rec_cluster)
        })
    per_true_cluster = pd.DataFrame(per_true).sort_values("true_cluster").reset_index(drop=True)

    # ---- Weighted summaries of fragmentation
    w_majority = np.average(per_true_cluster["majority_capture"], weights=per_true_cluster["n_points"])
    w_entropy  = np.average(per_true_cluster["pred_label_entropy_bits"], weights=per_true_cluster["n_points"])

    metrics = {
        # Primary: how well true clusters stay intact in ONE predicted cluster
        "completeness": float(c),                 # 1.0 means no true cluster was split
        "b3_recall": float(b3_recall),            # also rewards intactness of true clusters

        # Helpful companions / context
        "homogeneity": float(h),
        "v_measure": float(v),
        "ARI": float(ari),
        "NMI": float(nmi),

        # Fragmentation summaries (size-weighted)
        "weighted_majority_capture": float(w_majority),        # ↑ is better (max 1)
        "weighted_pred_label_entropy_bits": float(w_entropy),  # ↓ is better (min 0)
    }

    return metrics, per_true_cluster


def relabel_pred_for_reporting(
    y_true,
    y_pred,
    strategy="hungarian",         # "hungarian" or "majority"
    noise_labels=(-1, None, np.nan)
):
    """
    Remap y_pred labels into y_true label space for readability.
    Returns:
      y_pred_mapped : np.ndarray (same length as y_pred)
      mapping       : dict {pred_label -> true_label} (np.nan for unmapped/noise)
      contingency   : pandas.DataFrame (counts) indexed by true, columns by pred (after filtering noise)
    Notes:
      - Only used for *reporting/visualization*. Core clustering metrics don't require this.
      - "hungarian" gives a 1-1 mapping (up to min(#true,#pred)).
      - "majority" allows many predicted clusters to map to the same true label.
    """
    yt = pd.Series(y_true).reset_index(drop=True)
    yp = pd.Series(y_pred).reset_index(drop=True)

    # treat noise as NaN
    yp_clean = yp.copy()
    yp_clean = yp_clean.where(~yp_clean.isin(noise_labels), other=np.nan)

    mask = (~yt.isna()) & (~yp_clean.isna())
    yt_n = yt[mask].to_numpy()
    yp_n = yp_clean[mask].to_numpy()

    # Build contingency (true x pred)
    cont = pd.crosstab(pd.Series(yt_n, name="true"), pd.Series(yp_n, name="pred"))
    true_labels = cont.index.to_list()
    pred_labels = cont.columns.to_list()
    M = cont.to_numpy(dtype=float)

    mapping = {}
    if strategy == "hungarian":
        # We maximize overlap => minimize negative counts
        cost = -M
        r_idx, c_idx = linear_sum_assignment(cost)
        for ri, ci in zip(r_idx, c_idx):
            mapping[pred_labels[ci]] = true_labels[ri]
        # any pred labels not used get mapped by majority as a fallback
        unused = [pl for pl in pred_labels if pl not in mapping]
        for pl in unused:
            if cont[pl].sum() > 0:
                mapping[pl] = cont[pl].idxmax()
            else:
                mapping[pl] = np.nan

    elif strategy == "majority":
        for pl in pred_labels:
            if cont[pl].sum() > 0:
                mapping[pl] = cont[pl].idxmax()
            else:
                mapping[pl] = np.nan
    else:
        raise ValueError("strategy must be 'hungarian' or 'majority'")

    # Apply mapping back to full y_pred (including noise/NaN rows)
    def _map_one(v):
        if pd.isna(v) or v in noise_labels:
            return np.nan
        return mapping.get(v, np.nan)

    y_pred_mapped = yp.apply(_map_one).to_numpy()

    return y_pred_mapped, mapping, cont

# # 1) (Optional) remap for readable reports/plots
# y_pred_mapped, mapping, contingency = relabel_pred_for_reporting(
#     y_true, y_pred, strategy="hungarian"
# )
# print("Pred→True mapping:", mapping)
# print(contingency)

# # 2) Compute your completeness-focused metrics (label-invariant anyway)
# metrics, per_true = compute_cluster_cohesion(y_true, y_pred)   # from earlier
# # If you want per-cluster tables to show true→single predicted cluster clearly,
# # you can also run it on the mapped labels for nicer summaries:
# metrics_mapped, per_true_mapped = compute_cluster_cohesion(y_true, y_pred_mapped)
