"""R-vine copula modelling (ctypes wrapper for pyvinecop C++ backend)."""

from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import polars as pl


def fit(data: pl.DataFrame,
        family_set: List[str] = None,
        method: str = "mle") -> Dict[str, Any]:
    """
    Fit an R‑vine to data (assets in columns) via AIC family selection.

    Parameters
    ----------
    data : polars.DataFrame
        Assets in columns; must have ≥3 columns, none constant.
    family_set : List[str], optional
        Copula families to consider. Default ["gumbel", "joe", "t"].
    method : str
        Estimation method (only "mle" supported).

    Returns
    -------
    dict
        {"trees": [{"edges": [{"i", "j", "family", "theta", "tau"}]}],
         "npars": int, "aic": float, "loglik": float}

    Raises
    ------
    ValueError
        If data has <3 columns or any column is constant.
    """
    if family_set is None:
        family_set = ["gumbel", "joe", "t"]

    if data.shape[1] < 3:
        raise ValueError("data must have at least 3 columns")

    x = data.to_numpy()
    for i, name in enumerate(data.columns):
        if np.allclose(x[:, i], x[0, i]):
            raise ValueError(f"column '{name}' is constant")

    try:
        import pyvinecop as pv
    except ImportError:
        raise ImportError("pyvinecop not installed") from None

    fam_map = {n.lower(): getattr(pv.BicopFamily, n) for n in
               ["indep", "gaussian", "student", "clayton", "gumbel", "frank", "joe"]}

    controls = pv.FitControlsVinecop(
        family_set=[fam_map[f.lower()] for f in family_set if f.lower() in fam_map],
        parametric_method=method,
    )
    vc = pv.Vinecop(x, controls=controls)

    return {
        "trees": [
            {
                "edges": [
                    {
                        "i": int(e.indices[0]),
                        "j": int(e.indices[1]),
                        "family": e.copula.family_name,
                        "theta": float(e.copula.parameters[0]) if e.copula.parameters.size else 0.0,
                        "tau": float(e.copula.tau),
                    }
                    for e in (vc.get_edge(t, k) for k in range(vc.nedges))
                ]
            }
            for t in range(vc.dim - 1)
        ],
        "npars": vc.npars,
        "aic": vc.aic,
        "loglik": vc.loglik,
    }


def simulate(vine_dict: Dict[str, Any],
             n_draws: int = 10_000,
             seed: Optional[int] = None) -> pl.DataFrame:
    """
    Simulate uniforms from a fitted vine copula.

    Parameters
    ----------
    vine_dict : dict
        Vine specification from fit().
    n_draws : int
        Number of draws to generate (>0).
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    polars.DataFrame
        Simulated uniforms in [0,1]^d with asset columns.
    """
    if n_draws <= 0:
        raise ValueError("n_draws must be positive")

    try:
        import pyvinecop as pv
    except ImportError:
        raise ImportError("pyvinecop not installed") from None

    dim = len(vine_dict["trees"][0]["edges"]) + 1
    structure = pv.RVineStructure.simulate(dim)

    pair_copulas = [[None for _ in range(dim - t - 1)] for t in range(dim - 1)]
    for t, tree in enumerate(vine_dict["trees"]):
        for e in tree["edges"]:
            fam = getattr(pv.BicopFamily, e["family"].lower(), pv.BicopFamily.indep)
            pc = pv.Bicop(family=fam, parameters=[e["theta"]])
            pair_copulas[t][e["i"] - (t + 1)] = pc

    vc = pv.Vinecop(structure, pair_copulas)
    u = vc.simulate(n_draws, seed=seed)

    return pl.DataFrame(u, schema=[f"asset_{i}" for i in range(u.shape[1])])


def upper_tail_dependence(vine_dict: Dict[str, Any],
                          pair: Tuple[str, str]) -> float:
    """
    Compute analytical λ_U for a given pair.

    Parameters
    ----------
    vine_dict : dict
        Vine specification from fit().
    pair : Tuple[str, str]
        Pair of asset names, e.g. ("SPY", "VIX").

    Returns
    -------
    float
        Upper tail dependence λ_U in [0, 1].
    """
    import scipy.stats as stats

    i, j = (int(p.split("_")[1]) if p.startswith("asset_") else None for p in pair)
    if i is None or j is None:
        return 0.0

    for edge in vine_dict["trees"][0]["edges"]:
        if {edge["i"], edge["j"]} == {i, j}:
            fam, theta = edge["family"].lower(), edge["theta"]

            # Gumbel tail dependence
            if fam == "gumbel" and theta >= 1:
                return 2.0 - 2.0  ** (1.0 / theta)

            # Student‑t tail dependence (simplified)
            if fam == "student":
                rho = theta
                if abs(rho) < 1.0:
                    return 2.0 * stats.t.cdf(
                        -np.sqrt(3 * (1 - rho) / (1 + rho)), df=4
                    )

            return 0.0

    return 0.0
