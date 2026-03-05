import pandas as pd

BLENDING_THRESHOLD = 30
MIN_BLENDING_COUNT = 5
TARGET_GROUP_SIZE = 7
MIN_GROUP_SIZE = 5
MAX_GROUP_SIZE = 9
IDEAL_MIN_GROUP_SIZE = 6
IDEAL_MAX_GROUP_SIZE = 8


def _group_size_status(group_size):
    if IDEAL_MIN_GROUP_SIZE <= group_size <= IDEAL_MAX_GROUP_SIZE:
        return "Ideal (6-8)"
    if MIN_GROUP_SIZE <= group_size <= MAX_GROUP_SIZE:
        return "Allowed (5 or 9)"
    return "Outside range (not 5-9)"


def _choose_group_sizes(
    learner_count,
    target_group_size=TARGET_GROUP_SIZE,
    min_group_size=MIN_GROUP_SIZE,
    max_group_size=MAX_GROUP_SIZE,
):
    if learner_count <= 0:
        return []
    if learner_count <= max_group_size:
        return [learner_count]

    target_group_count = learner_count / target_group_size
    min_candidate = max(1, int(target_group_count) - 3)
    max_candidate = int(target_group_count) + 3

    best_sizes = []
    best_score = None

    for group_count in range(min_candidate, max_candidate + 1):
        if group_count <= 0:
            continue

        base_size = learner_count // group_count
        remainder = learner_count % group_count

        candidate_sizes = [base_size + 1] * remainder + [base_size] * (group_count - remainder)
        out_of_bounds_count = sum(
            size < min_group_size or size > max_group_size for size in candidate_sizes
        )
        distance_from_target = sum(abs(size - target_group_size) for size in candidate_sizes)
        spread = max(candidate_sizes) - min(candidate_sizes)
        group_count_distance = abs(group_count - target_group_count)

        score = (
            out_of_bounds_count,
            distance_from_target,
            spread,
            group_count_distance,
        )

        if best_score is None or score < best_score:
            best_score = score
            best_sizes = candidate_sizes

    if not best_sizes:
        return [learner_count]

    return best_sizes


def _assign_track_groups(
    track_df,
    group_type,
    sort_metric_column="letters_total_correct",
    target_group_size=TARGET_GROUP_SIZE,
    min_group_size=MIN_GROUP_SIZE,
    max_group_size=MAX_GROUP_SIZE,
):
    if track_df.empty:
        return track_df

    if sort_metric_column not in track_df.columns:
        track_df[sort_metric_column] = pd.NA

    # Use track-specific sorting metric, then fall back to letters score for stability.
    track_df["track_sort_metric"] = track_df[sort_metric_column]
    track_df["track_sort_metric"] = track_df["track_sort_metric"].fillna(
        track_df["letters_total_correct"]
    )

    sorted_track = track_df.sort_values(
        by=[
            "track_sort_metric",
            "letters_total_correct",
            "last_name",
            "first_name",
            "participant_key",
        ],
        ascending=[True, True, True, True, True],
    ).reset_index(drop=True)

    group_sizes = _choose_group_sizes(
        learner_count=len(sorted_track),
        target_group_size=target_group_size,
        min_group_size=min_group_size,
        max_group_size=max_group_size,
    )

    group_labels = []
    group_numbers = []
    position = 0
    for group_number, group_size in enumerate(group_sizes, start=1):
        for _ in range(group_size):
            if position >= len(sorted_track):
                break
            group_labels.append(f"{group_type[0]}{group_number}")
            group_numbers.append(group_number)
            position += 1

    assert len(group_labels) == len(sorted_track), "Every learner must receive a group label."

    sorted_track["group_type"] = group_type
    sorted_track["group_number"] = group_numbers
    sorted_track["group"] = group_labels
    sorted_track = sorted_track.drop(columns=["track_sort_metric"], errors="ignore")
    return sorted_track


def _assign_groups_for_class(
    class_df,
    blending_threshold=BLENDING_THRESHOLD,
    min_blending_count=MIN_BLENDING_COUNT,
    target_group_size=TARGET_GROUP_SIZE,
    min_group_size=MIN_GROUP_SIZE,
    max_group_size=MAX_GROUP_SIZE,
):
    if class_df.empty:
        return class_df

    class_df = class_df.copy()
    class_df["is_blending_eligible"] = class_df["letters_total_correct"] > blending_threshold

    blending_count = int(class_df["is_blending_eligible"].sum())
    letters_count = int(len(class_df) - blending_count)
    can_create_separate_blending_track = (
        blending_count >= min_blending_count
        and (letters_count == 0 or letters_count >= min_group_size)
    )

    if can_create_separate_blending_track:
        blending_track = _assign_track_groups(
            class_df[class_df["is_blending_eligible"]].copy(),
            group_type="Blending",
            sort_metric_column="words_total_correct",
            target_group_size=target_group_size,
            min_group_size=min_group_size,
            max_group_size=max_group_size,
        )
        letters_track = _assign_track_groups(
            class_df[~class_df["is_blending_eligible"]].copy(),
            group_type="Letters",
            sort_metric_column="letters_total_correct",
            target_group_size=target_group_size,
            min_group_size=min_group_size,
            max_group_size=max_group_size,
        )
        class_grouped = pd.concat([letters_track, blending_track], ignore_index=True)
    else:
        class_grouped = _assign_track_groups(
            class_df.copy(),
            group_type="Letters",
            sort_metric_column="letters_total_correct",
            target_group_size=target_group_size,
            min_group_size=min_group_size,
            max_group_size=max_group_size,
        )

    return class_grouped


def assign_groups_2026(
    df,
    blending_threshold=BLENDING_THRESHOLD,
    min_blending_count=MIN_BLENDING_COUNT,
    target_group_size=TARGET_GROUP_SIZE,
    min_group_size=MIN_GROUP_SIZE,
    max_group_size=MAX_GROUP_SIZE,
):
    required_columns = [
        "response_id",
        "participant_id",
        "class_name",
        "collected_by",
        "first_name",
        "last_name",
        "letters_total_correct",
        "response_date",
    ]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns for 2026 grouping: {missing_columns}")

    grouped_df = df.copy()
    grouped_df["response_date"] = pd.to_datetime(grouped_df["response_date"], errors="coerce")
    grouped_df["letters_total_correct"] = pd.to_numeric(
        grouped_df["letters_total_correct"], errors="coerce"
    )
    if "words_total_correct" in grouped_df.columns:
        grouped_df["words_total_correct"] = pd.to_numeric(
            grouped_df["words_total_correct"], errors="coerce"
        )
    else:
        grouped_df["words_total_correct"] = pd.NA
    grouped_df = grouped_df.dropna(
        subset=["class_name", "collected_by", "letters_total_correct"]
    ).copy()

    grouped_df["participant_id"] = grouped_df["participant_id"].astype(str).str.strip()
    grouped_df["participant_key"] = grouped_df["participant_id"]
    participant_id_missing = grouped_df["participant_key"].isin(["", "nan", "None"])
    grouped_df.loc[participant_id_missing, "participant_key"] = grouped_df.loc[
        participant_id_missing, "response_id"
    ].astype(str)

    grouped_df = grouped_df.sort_values(
        by=["participant_key", "response_date", "response_id"],
        ascending=[True, False, False],
    ).drop_duplicates(subset=["participant_key"], keep="first")

    grouped_class_dataframes = []
    for _, class_df in grouped_df.groupby(["class_name", "collected_by"], sort=False):
        class_grouped = _assign_groups_for_class(
            class_df=class_df,
            blending_threshold=blending_threshold,
            min_blending_count=min_blending_count,
            target_group_size=target_group_size,
            min_group_size=min_group_size,
            max_group_size=max_group_size,
        )
        grouped_class_dataframes.append(class_grouped)

    if not grouped_class_dataframes:
        return pd.DataFrame(columns=grouped_df.columns)

    grouped_df = pd.concat(grouped_class_dataframes, ignore_index=True)

    if grouped_df.empty:
        return grouped_df

    grouped_df["group_size"] = grouped_df.groupby(
        ["class_name", "collected_by", "group"]
    )["response_id"].transform("count")
    grouped_df["group_size_status"] = grouped_df["group_size"].map(_group_size_status)

    grouped_df = grouped_df.sort_values(
        by=[
            "program_name",
            "class_name",
            "collected_by",
            "group_type",
            "group_number",
            "letters_total_correct",
            "last_name",
            "first_name",
        ],
        ascending=[True, True, True, True, True, True, True, True],
    ).reset_index(drop=True)

    assert grouped_df["group"].notna().all(), "Grouping failed: missing group labels."
    assert grouped_df["group_size"].notna().all(), "Grouping failed: missing group sizes."

    return grouped_df


def build_group_size_summary(grouped_df):
    if grouped_df.empty:
        return pd.DataFrame()

    summary = (
        grouped_df.groupby(
            ["program_name", "class_name", "collected_by", "group_type", "group"]
        )
        .agg(
            group_size=("response_id", "count"),
            min_letters=("letters_total_correct", "min"),
            max_letters=("letters_total_correct", "max"),
        )
        .reset_index()
        .sort_values(
            by=["program_name", "class_name", "collected_by", "group_type", "group"],
            ascending=[True, True, True, True, True],
        )
    )
    summary["group_size_status"] = summary["group_size"].map(_group_size_status)
    return summary
