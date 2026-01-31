from typing import Any, cast
import logging
import numpy as np
from collections.abc import Sequence, Callable
from pathlib import Path
from ec_toolkit.io.vasp_helpers import read_reverse_order
from astropy import constants as const
from astropy import units as u
import warnings

# rust extension (built with maturin)
from ec_toolkit import _frequency_extraction as freq_ext

freq_ext: Any = cast(Any, freq_ext)
const: Any = cast(Any, const)
u: Any = cast(Any, u)


class OutcarParser:
    """
    Utilities for parsing VASP OUTCAR files and computing vibrational corrections.

    Notes
    -----
    - Energies returned are *per molecule/mode* (not per mole) and expressed in eV unless
      otherwise noted. This keeps them directly addable to single-unit DFT energies
      expressed in eV.
    - By default a frequency-floor of 50 cm^-1 is *only* applied to the entropy
      (T*S) calculation (this mirrors ASE's common policy). Use
      ``apply_floor_to_enthalpy=True`` to also apply the floor when computing the
      vibrational thermal enthalpy if you prefer that behaviour.
    """

    T: float = 298.15  # default temperature (K)

    # lightweight cache for read_reverse_order results: key -> tuple of lines
    _tail_cache: dict[str, list[str]] = {}

    # module-level logger dedicated to this class
    logger: logging.Logger = logging.getLogger("OutcarParser")

    @classmethod
    def enable_logging(cls, level: int = logging.INFO) -> None:
        """
        Enable console logging for the class logger.

        Adds a StreamHandler only if no handlers are present to avoid duplicate
        messages when called multiple times.
        """
        cls.logger.setLevel(level)
        if not cls.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("[OutcarParser] %(levelname)s: %(message)s")
            )
            cls.logger.addHandler(handler)
        cls.logger.propagate = False

    @classmethod
    def disable_logging(cls) -> None:
        """Disable the class logger (remove handlers)."""
        for h in list(cls.logger.handlers):
            cls.logger.removeHandler(h)
        cls.logger.setLevel(logging.WARNING)
        cls.logger.propagate = True

    @classmethod
    def _read_tail(cls, path: Path, max_lines: int = 200) -> list[str]:
        """
        Read the last `max_lines` lines using read_reverse_order and cache the result.

        This avoids repeatedly re-parsing large OUTCAR files when multiple
        small parsers (e.g. EDFT and convergence checks) are run on the same file.
        """
        key = f"{path.as_posix()}::{max_lines}"
        cached = cls._tail_cache.get(key)
        if cached is not None:
            return cached
        lines = list(read_reverse_order(path, max_lines=max_lines))
        cls._tail_cache[key] = lines
        return lines

    @classmethod
    def read_converged(cls, path: Path) -> bool:
        """
        Check whether an OUTCAR reached ionic convergence.

        Uses the tail cache to avoid re-reading the file multiple times when
        callers also parse other items from the same OUTCAR.
        """
        lines = cls._read_tail(path, max_lines=200)
        res = any("reached required accuracy" in line.lower() for line in lines[:200])
        cls.logger.info("Convergence check for %s: %s", path, res)
        return res

    @classmethod
    def read_edft(cls, path: Path) -> float:
        """
        Read the electronic energy from an OUTCAR by scanning backwards for 'sigma'.

        Returns the last token of the last matching line as float. Raises RuntimeError
        if no such line is found. Logs the found energy at INFO level when enabled.
        """
        lines = cls._read_tail(path, max_lines=2000)
        for line in lines:
            if "sigma" in line.lower():
                try:
                    val = float(line.split()[-1])
                except Exception:
                    cls.logger.warning(
                        "Found 'sigma' line but failed to parse value in %s", path
                    )
                    raise
                cls.logger.info("Electronic energy (sigma) from %s: %.8f", path, val)
                return val
        cls.logger.error("No electronic energy ('sigma') line found in %s", path)
        raise RuntimeError(f"No electronic energy ('sigma') line found in {path!r}")

    @classmethod
    def calc_corr(
        cls,
        path: Path,
        calc_tds: bool = True,
        floor_freq_cm: float = 50.0,
        apply_floor_to_enthalpy: bool = False,
    ) -> tuple[float, bool]:
        """
        Calculate the *total vibrational correction* (G - E_DFT) from an OUTCAR.

        The returned value ``corr_eV`` is:

            corr_eV = ZPE + E_vib_thermal - T * S_vib

        and is expressed in **eV per molecule** (so it can be added directly to a
        single-unit DFT energy expressed in eV). The boolean ``has_imag`` flags
        whether imaginary modes were detected and are therefore excluded from the
        sums.

        Although only ``corr_eV`` and ``has_imag`` are returned (as requested),
        the method logs the component values (ZPE, E_vib_thermal, T*S) at INFO
        level so users can inspect them when logging is enabled.
        """
        # Input validation
        if not isinstance(path, Path):
            raise TypeError("path must be a pathlib.Path")
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"OUTCAR not found at {path!r}")

        # Attempt to use the Rust-accelerated extractor (preferred)
        freqs_cm_real: list[float] = []
        has_imag = False
        try:
            # prefer the backwards/tail-optimized function (fast)
            freqs_cm_real, has_imag = freq_ext.extract_frequencies_backwards(
                path.as_posix()
            )
        except Exception as exc:
            # log and try the simpler extractor
            cls.logger.warning(
                "Rust extractor (backwards) failed for %s: %s; trying fallback extractor",
                path,
                exc,
            )
            try:
                freqs_cm_real, has_imag = freq_ext.extract_frequencies(path.as_posix())
            except Exception as exc2:
                cls.logger.warning(
                    "Rust extractor (fallback) failed for %s: %s", path, exc2
                )

        if len(freqs_cm_real) == 0:
            cls.logger.info(
                "No real positive frequencies found in %s (has_imag=%s)", path, has_imag
            )
            return 0.0, bool(has_imag)

        # convert to numpy array (cm^-1)
        freqs_cm_arr = np.array(freqs_cm_real, dtype=float)

        # convert to Hz
        freqs_hz = (u.Quantity(freqs_cm_arr, u.cm**-1) * const.c).to(u.Hz)

        # ZPE: 0.5 * h * nu per mode
        zpe_j = (0.5 * const.h * freqs_hz).sum()
        zpe_eV = float(zpe_j.to(u.eV).value)

        # Temperature quantity and dimensionless x = h nu / (k_B T)
        T_q = OutcarParser.T * u.K

        # For entropy we allow flooring the low-frequency modes
        if floor_freq_cm and floor_freq_cm > 0.0:
            freqs_floor_cm = np.maximum(freqs_cm_arr, floor_freq_cm)
            freqs_floor_hz = (u.Quantity(freqs_floor_cm, u.cm**-1) * const.c).to(u.Hz)
        else:
            freqs_floor_hz = freqs_hz

        # Compute T*S (may be skipped if calc_tds is False)
        if calc_tds:
            x_entropy = (const.h * freqs_floor_hz) / (const.k_B * T_q)
            x_e = x_entropy.value
            with np.errstate(
                over="ignore", under="ignore", divide="ignore", invalid="ignore"
            ):
                denom = np.expm1(x_e)
                term1 = np.where(denom != 0.0, x_e / denom, 1.0)
                term2 = np.log1p(-np.exp(-x_e))
                s_per_mode = const.k_B * (term1 - term2)

            s_total = u.Quantity(s_per_mode).sum()
            tds_j = (s_total * T_q).to(u.J)
            tds_eV = float(tds_j.to(u.eV).value)
        else:
            tds_eV = 0.0

        # Thermal enthalpy E_vib = sum( h nu/(exp(x)-1) ) = k_B T * term1 per mode
        enthalpy_hz = freqs_floor_hz if apply_floor_to_enthalpy else freqs_hz
        x_ent = (const.h * enthalpy_hz) / (const.k_B * T_q)
        x_val = x_ent.value
        with np.errstate(
            over="ignore", under="ignore", divide="ignore", invalid="ignore"
        ):
            denom = np.expm1(x_val)
            term1 = np.where(denom != 0.0, x_val / denom, 1.0)
            e_therm_per_mode = const.k_B * T_q * term1

        e_therm_total_j = u.Quantity(e_therm_per_mode).sum()
        e_therm_eV = float(e_therm_total_j.to(u.eV).value)

        # Final correction: ZPE + E_therm - T*S
        corr_eV = float(zpe_eV + e_therm_eV - tds_eV)

        # Log component values at INFO level so users can inspect them when logging
        if cls.logger.isEnabledFor(logging.INFO):
            if has_imag:
                cls.logger.warning(
                    "Imaginary modes were detected in %s; they were excluded from sums",
                    path,
                )
            else:
                cls.logger.info("No imaginary modes were detected in %s", path)
            cls.logger.info("Parsed %d real vibrational modes", len(freqs_cm_arr))
            cls.logger.info("ZPE = %.6f eV", zpe_eV)
            cls.logger.info("E_vib_thermal = %.6f eV", e_therm_eV)
            cls.logger.info("T*S_vib = %.6f eV", tds_eV)
            cls.logger.info(
                "Total vibrational correction (ZPE + E_th - T*S) = %.6f eV", corr_eV
            )

        return corr_eV, bool(has_imag)

    @classmethod
    def auto_read(
        cls,
        workdir: Path,
        subdirs: Sequence[str],
        *,
        calc_tds: bool = False,
        zpe_locator: Callable[[Path, str], Path] | None = None,
        check_structure: bool = False,
        floor_freq_cm: float = 50.0,
        apply_floor_to_enthalpy: bool = False,
    ) -> tuple[list[float], list[float], list[bool | None]]:
        """
        Collect EDFT and vibrational corrections for `subdirs` under `workdir`.

        Returns
        -------
        If check_structure is False:
            (edft_list, corr_list)
        If check_structure is True:
            (edft_list, corr_list, check_list)

        """
        # default zpe_locator
        if zpe_locator is None:

            def zpe_locator(wd: Path, d: str) -> Path:
                return wd / d / "zpe" / "OUTCAR"

        edfts: list[float] = []
        corrs: list[float] = []
        checks: list[bool | None] = []

        for d in subdirs:
            base = workdir / d
            efile = base / "OUTCAR"

            # convergence of the energy run itself
            is_conv = cls.read_converged(efile)

            # EDFT (raises if not found / parse fails)
            edft = cls.read_edft(efile)
            edfts.append(edft)

            # Vibrational correction
            zfile = zpe_locator(workdir, d)
            if zfile.exists():
                corr, has_imag = cls.calc_corr(
                    zfile,
                    calc_tds=calc_tds,
                    floor_freq_cm=floor_freq_cm,
                    apply_floor_to_enthalpy=apply_floor_to_enthalpy,
                )
            else:
                warnings.warn(
                    f"No ZPE/TdS OUTCAR found at {zfile!r}; setting correction to 0",
                    UserWarning,
                    stacklevel=2,
                )
                corr, has_imag = 0.0, True

            corrs.append(corr)

            # final "check_structure" boolean: True only if converged AND no imag freqs
            checks.append(bool(is_conv and (not bool(has_imag))))

        if not check_structure:
            # cast the list[None] to the annotated list[bool|None] so the type checker is happy
            from typing import cast as _cast

            checks = _cast(list[bool | None], [None] * len(edfts))

        return edfts, corrs, checks
