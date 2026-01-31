from dataclasses import dataclass
import numpy as np
import warnings


class Compound:
    """Models a chemical species with its reference energies and convergence metadata."""

    def __init__(
        self,
        formula: str,
        reference_energies: dict[str, float],
        converged: bool | None = True,
    ) -> None:
        # Input validation
        if not isinstance(formula, str):
            raise TypeError("formula must be a str")
        if not isinstance(reference_energies, dict):
            raise TypeError("reference_energies must be a dict[str, float]")

        # Coerce & validate reference energies into a defensive copy
        refs: dict[str, float] = {}
        for k, v in reference_energies.items():
            if not isinstance(k, str):
                raise TypeError("reference_energies keys must be strings")
            try:
                refs[k] = float(v)
            except Exception as exc:
                raise TypeError(
                    f"reference_energies[{k!r}] is not float-coercible: {exc}"
                ) from exc

        if not (isinstance(converged, bool) or converged is None):
            raise TypeError("converged must be a bool or None")

        self.formula = formula
        self.reference_energies = refs
        self.converged = converged

    def energy(self, kind: str = "dft") -> float:
        """Return stored reference energy for `kind`. Missing keys -> 0.0."""
        if not isinstance(kind, str):
            raise TypeError("kind must be a str")
        return float(self.reference_energies.get(kind, 0.0))

    def __repr__(self) -> str:
        refs = ", ".join(f"{k}={v:.3f}" for k, v in self.reference_energies.items())
        if self.converged is None:
            status = "Not checked"
        else:
            status = "Converged" if self.converged else "Failed"
        return f"{self.formula}({refs}, status={status})"


@dataclass
class ElementaryStep:
    """
    Elementary chemical step.

    Attributes
    ----------
    stoich : dict
        Mapping Compound -> coefficient (products positive).
    label : str
        Human label.
    is_electrochemical : bool
        True if the step involves electron transfer.
    apply_correction : bool
        If True, this is the correction step; properties `.d_e` and `.d_corr` raise
        AttributeError to intentionally hide the values for the correction step.
    """

    stoich: dict
    label: str
    is_electrochemical: bool = False
    apply_correction: bool = False

    def __repr__(self) -> str:
        prods = [(c, v) for c, v in self.stoich.items() if v > 0]
        reacs = [(c, v) for c, v in self.stoich.items() if v < 0]
        parts = []
        for comp, coeff in prods + reacs:
            parts.append(f"{coeff:+g} {comp.formula}")
        return " ".join(parts)

    @property
    def d_e(self) -> float:
        """Electronic energy change (eV) for the step (products - reactants)."""
        if self.apply_correction:
            raise AttributeError(
                "d_e is not available for an ElementaryStep with apply_correction=True"
            )
        return sum(comp.energy("dft") * coeff for comp, coeff in self.stoich.items())

    @property
    def d_corr(self) -> float:
        """
        Vibrational correction contribution (eV), i.e. the combined correction
        returned by OutcarParser.calc_corr (ZPE + E_therm - T*S).
        """
        if self.apply_correction:
            raise AttributeError(
                "d_corr is not available for an ElementaryStep with apply_correction=True"
            )
        return sum(comp.energy("corr") * coeff for comp, coeff in self.stoich.items())


class Mechanism:
    """
    Mechanism: ordered list of ElementaryStep objects.

    Constructor:
      Mechanism(steps: list[ElementaryStep], eq_pot: float, sym_fac: int = 1,
                ref_el: str = "RHE", *, is_oxidation_reaction: bool)

    Caching behaviour:
      - step_dg_array(...) and reaction_intermediate_free_energies(...) are cached.
      - caches keyed by sym_fac (calls with different sym_fac recompute).
      - call invalidate_cache() to force recompute.
    """

    def __init__(
        self,
        steps: list[ElementaryStep],
        eq_pot: float,
        sym_fac: int = 1,
        ref_el: str = "RHE",
        *,
        is_oxidation_reaction: bool,
    ) -> None:
        # validation
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError(
                "`steps` must be a non-empty list of ElementaryStep instances."
            )
        for idx, s in enumerate(steps):
            if not isinstance(s, ElementaryStep):
                raise TypeError(
                    f"steps[{idx}] is not an ElementaryStep (got {type(s)})"
                )

        if not isinstance(eq_pot, (int, float)):
            raise TypeError("`eq_pot` must be a number (int or float).")
        if not isinstance(sym_fac, int) or sym_fac < 1:
            raise ValueError("`sym_fac` must be a positive integer")
        if not isinstance(ref_el, str) or ref_el.strip() == "":
            raise ValueError("`ref_el` must be a non-empty string")
        if not isinstance(is_oxidation_reaction, bool):
            raise TypeError("`is_oxidation_reaction` must be a boolean")

        # enforce uniqueness of apply_correction==True
        n_corrections = sum(1 for s in steps if bool(s.apply_correction))
        if n_corrections > 1:
            raise ValueError(
                "At most one ElementaryStep in a Mechanism may have apply_correction=True"
            )

        self.steps = steps
        self.eq_pot = float(eq_pot)
        self.sym_fac = sym_fac
        self.ref_el = ref_el
        self.is_oxidation_reaction = is_oxidation_reaction
        self.el_steps = [step.is_electrochemical for step in steps]
        self.labels = [step.label for step in steps]

        # caches: None until computed (use | None syntax)
        self._cached_step_dg: np.ndarray | None = None
        self._cached_sym_fac: int | None = None
        self._cached_reaction_intermediate_free: np.ndarray | None = None

        # warn if no correction step provided (user explicitly requested no correction)
        if n_corrections == 0:
            default_idx = (len(self.steps) - 1) if self.is_oxidation_reaction else 0
            warnings.warn(
                "No ElementaryStep has apply_correction=True. "
                "No gas phase correction (top-up) will be applied automatically. "
                f"(Historical default would place correction at index {default_idx} "
                f"({'last' if self.is_oxidation_reaction else 'first'} step) — "
                "set apply_correction=True on that step to enable it.)",
                UserWarning,
            )

    def invalidate_cache(self) -> None:
        """Clear cached dg and intermediate free-energy arrays so they will be recomputed."""
        self._cached_step_dg = None
        self._cached_sym_fac = None
        self._cached_reaction_intermediate_free = None

    @property
    def dE_array(self) -> np.ndarray:
        """
        Per-step electronic-energy differences (eV).
        If a step does not expose `.d_e` (e.g. apply_correction=True), that
        position contains np.nan instead of raising.
        """
        out = []
        for s in self.steps:
            try:
                out.append(float(s.d_e))
            except AttributeError:
                # step intentionally hides d_e for correction — return NaN
                out.append(np.nan)
            except Exception:
                # any other problem coercing to float -> NaN
                out.append(np.nan)
        return np.array(out, dtype=float)

    @property
    def dCORR_array(self) -> np.ndarray:
        """
        Per-step CORR contributions (eV). np.nan where unavailable.
        """
        out = []
        for s in self.steps:
            try:
                out.append(float(s.d_corr))
            except AttributeError:
                out.append(np.nan)
            except Exception:
                out.append(np.nan)
        return np.array(out, dtype=float)

    def set_labels(self, new_labels: list[str]) -> None:
        if len(new_labels) != len(self.steps):
            raise ValueError("Label count mismatch")
        self.labels = new_labels

    @property
    def n_steps(self) -> int:
        return len(self.steps)

    @property
    def correction_index(self) -> int | None:
        """Return index of step with apply_correction True, or None."""
        for idx, s in enumerate(self.steps):
            if s.apply_correction:
                return idx
        return None

    def step_dg_array(self, sym_fac: int | None = None) -> np.ndarray:
        """
        Compute (or return cached) per-step zero-bias ΔG array of length N.

        Caching:
          - If cached and requested sym_fac equals cached sym_fac -> return cached copy.
          - Otherwise compute, cache, and return a copy.
        """
        if sym_fac is None:
            sym_fac = self.sym_fac

        # if cache present and sym_fac matches, return cached copy
        if self._cached_step_dg is not None and self._cached_sym_fac == sym_fac:
            return self._cached_step_dg.copy()

        # compute dg (same logic as before)
        N = len(self.steps)
        if N == 0:
            arr = np.array([], dtype=float)
            # store cache
            self._cached_step_dg = arr.copy()
            self._cached_sym_fac = sym_fac
            self._cached_reaction_intermediate_free = None
            return arr

        dg = np.empty(N, dtype=float)
        for i, s in enumerate(self.steps):
            if s.apply_correction:
                dg[i] = 0.0
            else:
                d_e = float(s.d_e)
                d_corr = float(s.d_corr)
                dg[i] = (d_e + d_corr) / float(sym_fac)

        # compute number of electrons with sign convention
        n_e = int(sum(1 if s.is_electrochemical else 0 for s in self.steps))
        if not self.is_oxidation_reaction:
            n_e = -n_e
        G_eq = float(self.eq_pot) * n_e

        corr_idx = self.correction_index
        if corr_idx is None:
            # no top-up applied; store cache and return
            self._cached_step_dg = dg.copy()
            self._cached_sym_fac = sym_fac
            # invalidate reaction intermediate free cache (dependent on dg)
            self._cached_reaction_intermediate_free = None
            return dg.copy()

        # apply top-up at corr_idx
        if N == 1:
            dg[0] = G_eq
        else:
            other_sum = float(dg.sum() - dg[corr_idx])
            dg[corr_idx] = G_eq - other_sum

        # cache and return copy
        self._cached_step_dg = dg.copy()
        self._cached_sym_fac = sym_fac
        self._cached_reaction_intermediate_free = None
        return dg.copy()

    def reaction_intermediate_free_energies(
        self, sym_fac: int | None = None
    ) -> np.ndarray:
        """
        Return cumulative free energies of intermediates. length = N+1 with first value 0.0.
        Uses caching keyed by sym_fac.
        """
        if sym_fac is None:
            sym_fac = self.sym_fac

        # if cached and matches sym_fac, return copy
        if (
            self._cached_reaction_intermediate_free is not None
            and self._cached_sym_fac == sym_fac
        ):
            return self._cached_reaction_intermediate_free.copy()

        # ensure step dg cached/available
        dg = self.step_dg_array(
            sym_fac=sym_fac
        )  # this will update self._cached_step_dg/_sym_fac

        rif = np.concatenate(([0.0], np.cumsum(dg)))
        # cache and return copy
        self._cached_reaction_intermediate_free = rif.copy()
        self._cached_sym_fac = sym_fac
        return rif.copy()
