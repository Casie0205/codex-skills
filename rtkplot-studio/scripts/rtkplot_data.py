from __future__ import annotations

import math
import statistics
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

REQUIRED_COLUMNS = 18
DEFAULT_PLOT_FIX_TYPES = frozenset((1, 2, 3))
FIX_TYPE_NAMES = {
    1: "RTKFIX",
    2: "RTKFLOAT",
    3: "SINGLE",
    4: "NO_SOLUTION",
}

WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)


class RtkPlotError(ValueError):
    pass


@dataclass(frozen=True)
class RtkSample:
    time_s: float
    lat_rad: float
    lon_rad: float
    h_m: float
    sigma_lat_m: float
    sigma_lon_m: float
    sigma_h_m: float
    diff_age_s: float
    sol_age_s: float
    num_svs: int | None
    best_sol_status_code: int | None
    best_pos_type_code: int | None
    gnssfgo_type_code: int | None
    pdop: float
    hdop: float
    vdop: float
    pos_source_code: int | None
    hpd_status_code: int | None

    @property
    def fix_name(self) -> str:
        return fix_type_name(self.gnssfgo_type_code)

    def has_valid_position(self) -> bool:
        return all(math.isfinite(value) for value in (self.lat_rad, self.lon_rad, self.h_m))

    def has_finite_sigma(self) -> bool:
        return all(
            math.isfinite(value)
            for value in (self.sigma_lat_m, self.sigma_lon_m, self.sigma_h_m)
        )


@dataclass
class RtkDataset:
    path: Path
    samples: list[RtkSample]
    skipped_rows: int
    malformed_rows: int
    row_column_counts: Counter[int]

    @property
    def name(self) -> str:
        return self.path.stem


@dataclass(frozen=True)
class EnuPosition:
    east_m: float
    north_m: float
    up_m: float


def fix_type_name(code: int | None) -> str:
    if code is None:
        return "UNKNOWN"
    return FIX_TYPE_NAMES.get(code, f"UNKNOWN_{code}")


def _float_token(tokens: Sequence[str], index: int) -> float:
    return float(tokens[index])


def _code_token(tokens: Sequence[str], index: int) -> int | None:
    value = float(tokens[index])
    if not math.isfinite(value):
        return None
    return round(value)


def parse_rtkplot(path: Path) -> RtkDataset:
    samples: list[RtkSample] = []
    row_column_counts: Counter[int] = Counter()
    skipped_rows = 0
    malformed_rows = 0

    try:
        with path.open("r", encoding="utf-8-sig", errors="replace") as stream:
            for raw_line in stream:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                tokens = line.split()
                row_column_counts[len(tokens)] += 1
                if len(tokens) < REQUIRED_COLUMNS:
                    malformed_rows += 1
                    skipped_rows += 1
                    continue

                try:
                    time_s = _float_token(tokens, 0)
                    if not math.isfinite(time_s):
                        raise ValueError("non-finite timestamp")
                    sample = RtkSample(
                        time_s=time_s,
                        lat_rad=_float_token(tokens, 1),
                        lon_rad=_float_token(tokens, 2),
                        h_m=_float_token(tokens, 3),
                        sigma_lat_m=_float_token(tokens, 4),
                        sigma_lon_m=_float_token(tokens, 5),
                        sigma_h_m=_float_token(tokens, 6),
                        diff_age_s=_float_token(tokens, 7),
                        sol_age_s=_float_token(tokens, 8),
                        num_svs=_code_token(tokens, 9),
                        best_sol_status_code=_code_token(tokens, 10),
                        best_pos_type_code=_code_token(tokens, 11),
                        gnssfgo_type_code=_code_token(tokens, 12),
                        pdop=_float_token(tokens, 13),
                        hdop=_float_token(tokens, 14),
                        vdop=_float_token(tokens, 15),
                        pos_source_code=_code_token(tokens, 16),
                        hpd_status_code=_code_token(tokens, 17),
                    )
                except (TypeError, ValueError):
                    malformed_rows += 1
                    skipped_rows += 1
                    continue

                samples.append(sample)
    except OSError as exc:
        raise RtkPlotError(f"cannot read RTKPlot input: {path}: {exc}") from exc

    if not samples:
        raise RtkPlotError(
            f"no usable 18-column RTKPlot rows found in {path}; "
            "this is not an RTKLIB .pos/.obs/.nav file"
        )

    samples.sort(key=lambda sample: sample.time_s)
    return RtkDataset(
        path=path,
        samples=samples,
        skipped_rows=skipped_rows,
        malformed_rows=malformed_rows,
        row_column_counts=row_column_counts,
    )


def finite_values(values: Iterable[float]) -> list[float]:
    return [value for value in values if math.isfinite(value)]


def value_range(values: Iterable[float], digits: int = 6) -> list[float | None]:
    usable = finite_values(values)
    if not usable:
        return [None, None]
    return [round(min(usable), digits), round(max(usable), digits)]


def choose_origin(dataset: RtkDataset) -> RtkSample:
    for sample in dataset.samples:
        if (
            sample.has_valid_position()
            and sample.gnssfgo_type_code is not None
            and sample.gnssfgo_type_code in DEFAULT_PLOT_FIX_TYPES
        ):
            return sample
    raise RtkPlotError(
        f"no finite RTKFIX/RTKFLOAT/SINGLE position in {dataset.path}"
    )


def summarize_dataset(dataset: RtkDataset) -> dict[str, object]:
    samples = dataset.samples
    times = [sample.time_s for sample in samples]
    deltas = [times[index] - times[index - 1] for index in range(1, len(times))]
    positive_deltas = [delta for delta in deltas if delta > 0.0]
    duration_s = times[-1] - times[0] if len(times) > 1 else 0.0
    fix_counts = Counter(sample.fix_name for sample in samples)
    status_counts = Counter(
        str(sample.best_sol_status_code)
        if sample.best_sol_status_code is not None
        else "unknown"
        for sample in samples
    )
    try:
        origin = choose_origin(dataset)
        origin_json = {
            "latitude_rad": round(origin.lat_rad, 12),
            "longitude_rad": round(origin.lon_rad, 12),
            "height_m": round(origin.h_m, 6),
        }
    except RtkPlotError:
        origin_json = None

    return {
        "path": str(dataset.path),
        "samples": len(samples),
        "skipped_rows": dataset.skipped_rows,
        "malformed_rows": dataset.malformed_rows,
        "row_column_counts": {
            str(width): count for width, count in sorted(dataset.row_column_counts.items())
        },
        "duration_seconds": round(duration_s, 6),
        "mean_dt_seconds": round(statistics.fmean(positive_deltas), 6)
        if positive_deltas
        else 0.0,
        "duplicate_timestamps": len(deltas) - len(positive_deltas),
        "valid_position_samples": sum(sample.has_valid_position() for sample in samples),
        "plottable_position_samples": sum(
            sample.has_valid_position()
            and sample.gnssfgo_type_code is not None
            and sample.gnssfgo_type_code in DEFAULT_PLOT_FIX_TYPES
            for sample in samples
        ),
        "finite_sigma_samples": sum(sample.has_finite_sigma() for sample in samples),
        "fix_type_counts": dict(sorted(fix_counts.items())),
        "best_sol_status_counts": dict(sorted(status_counts.items())),
        "latitude_rad_range": value_range((sample.lat_rad for sample in samples), 12),
        "longitude_rad_range": value_range((sample.lon_rad for sample in samples), 12),
        "height_m_range": value_range((sample.h_m for sample in samples), 6),
        "origin": origin_json,
    }


def ecef_from_llh(lat_rad: float, lon_rad: float, h_m: float) -> tuple[float, float, float]:
    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    sin_lon = math.sin(lon_rad)
    cos_lon = math.cos(lon_rad)
    radius = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    x = (radius + h_m) * cos_lat * cos_lon
    y = (radius + h_m) * cos_lat * sin_lon
    z = (radius * (1.0 - WGS84_E2) + h_m) * sin_lat
    return x, y, z


def enu_from_llh(
    lat_rad: float,
    lon_rad: float,
    h_m: float,
    origin_lat_rad: float,
    origin_lon_rad: float,
    origin_h_m: float,
) -> EnuPosition:
    x, y, z = ecef_from_llh(lat_rad, lon_rad, h_m)
    x0, y0, z0 = ecef_from_llh(origin_lat_rad, origin_lon_rad, origin_h_m)
    dx = x - x0
    dy = y - y0
    dz = z - z0

    sin_lat = math.sin(origin_lat_rad)
    cos_lat = math.cos(origin_lat_rad)
    sin_lon = math.sin(origin_lon_rad)
    cos_lon = math.cos(origin_lon_rad)
    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return EnuPosition(east_m=east, north_m=north, up_m=up)


def plottable_samples(
    dataset: RtkDataset,
    allowed_fix_types: frozenset[int] = DEFAULT_PLOT_FIX_TYPES,
) -> list[RtkSample]:
    return [
        sample
        for sample in dataset.samples
        if sample.has_valid_position()
        and sample.gnssfgo_type_code is not None
        and sample.gnssfgo_type_code in allowed_fix_types
    ]
