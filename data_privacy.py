from __future__ import annotations

import hashlib
import re
import pandas as pd
import streamlit as st


CHILD_FULL_COLUMNS = {
    "full_name",
    "full_names",
    "name_full",
    "name_learner_full",
    "participant_name",
}
CHILD_FIRST_COLUMNS = {
    "name",
    "first_name",
    "name_first_learner",
    "participant_firstname",
}
CHILD_LAST_COLUMNS = {
    "surname",
    "last_name",
    "name_second_learner",
    "participant_lastname",
}
CHILD_ID_COLUMNS = {
    "learner_id",
    "participant_id",
}

STAFF_FULL_COLUMNS = {
    "ea_name",
    "name_ta",
    "name_ta_rep",
    "name_and_surname",
    "user_name",
    "collected_by",
    "username",
}
STAFF_FIRST_COLUMNS = {
    "name_first_ta",
    "user_firstname",
}
STAFF_LAST_COLUMNS = {
    "name_second_ta",
    "user_lastname",
}

MENTOR_FULL_COLUMNS = {
    "mentor",
    "mentor_name",
}

SCHOOL_COLUMNS = {
    "school",
    "school_name",
    "school_rep",
    "school_rep_orig",
    "program_name",
    "org_name",
}

CLASS_COLUMNS = {
    "class",
    "class_name",
}

GROUP_COLUMNS = {
    "group",
    "group_name",
}

HIGH_RISK_EXACT_COLUMNS = {
    "instance_name",
    "instanceid",
    "learner_list",
    "learner_list_concat",
    "stage1_id_list",
    "stage1_name_list",
    "stage2_name_list",
    "stage1_join_list",
    "stage2_join_list",
}
HIGH_RISK_TEXT_TOKEN_SETS = (
    {"comments"},
    {"commentary"},
    {"note"},
    {"notes"},
    {"session", "text"},
    {"free", "text"},
    {"reason"},
    {"description"},
    {"detail"},
    {"details"},
    {"explain"},
)


def is_authenticated() -> bool:
    return bool(st.session_state.get("user"))


def mask_dataframe(
    df: pd.DataFrame | None,
    dataset_key: str | None = None,
    authenticated: bool | None = None,
) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    if authenticated is None:
        authenticated = is_authenticated()
    if authenticated or df.empty:
        return df.copy()

    masked_df = df.copy()
    normalized_columns = {column: _normalize_column_name(column) for column in masked_df.columns}
    _mask_entity_family(
        masked_df,
        normalized_columns,
        prefix="Child",
        full_columns=CHILD_FULL_COLUMNS,
        first_columns=CHILD_FIRST_COLUMNS,
        last_columns=CHILD_LAST_COLUMNS,
        id_columns=CHILD_ID_COLUMNS,
    )
    _mask_entity_family(
        masked_df,
        normalized_columns,
        prefix="TA",
        full_columns=STAFF_FULL_COLUMNS,
        first_columns=STAFF_FIRST_COLUMNS,
        last_columns=STAFF_LAST_COLUMNS,
    )
    _mask_entity_family(
        masked_df,
        normalized_columns,
        prefix="Mentor",
        full_columns=MENTOR_FULL_COLUMNS,
    )
    _mask_entity_family(
        masked_df,
        normalized_columns,
        prefix="School",
        full_columns=SCHOOL_COLUMNS,
    )
    _mask_entity_family(
        masked_df,
        normalized_columns,
        prefix="Class",
        full_columns=CLASS_COLUMNS,
    )
    _mask_entity_family(
        masked_df,
        normalized_columns,
        prefix="Group",
        full_columns=GROUP_COLUMNS,
    )

    _mask_high_risk_text_columns(masked_df, normalized_columns)
    _mask_dataset_specific_columns(masked_df, normalized_columns, dataset_key)
    return masked_df


def _normalize_column_name(column_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(column_name).strip().lower()).strip("_")


def _clean_text_value(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    return text


def _build_identifier_series(
    df: pd.DataFrame,
    normalized_columns: dict[str, str],
    full_columns: set[str],
    first_columns: set[str],
    last_columns: set[str],
    id_columns: set[str],
) -> pd.Series:
    identifier = pd.Series(pd.NA, index=df.index, dtype="object")

    for raw_column, normalized_column in normalized_columns.items():
        if normalized_column in full_columns or normalized_column in id_columns:
            series = df[raw_column].map(_clean_text_value)
            identifier = identifier.where(identifier.notna(), series)

    first_series = pd.Series(pd.NA, index=df.index, dtype="object")
    last_series = pd.Series(pd.NA, index=df.index, dtype="object")

    for raw_column, normalized_column in normalized_columns.items():
        if normalized_column in first_columns:
            series = df[raw_column].map(_clean_text_value)
            first_series = first_series.where(first_series.notna(), series)
        elif normalized_column in last_columns:
            series = df[raw_column].map(_clean_text_value)
            last_series = last_series.where(last_series.notna(), series)

    combined = (
        first_series.fillna("").astype(str).str.strip()
        + " "
        + last_series.fillna("").astype(str).str.strip()
    ).str.strip()
    combined = combined.replace("", pd.NA)
    identifier = identifier.where(identifier.notna(), combined)
    return identifier


def _mask_entity_family(
    df: pd.DataFrame,
    normalized_columns: dict[str, str],
    prefix: str,
    full_columns: set[str],
    first_columns: set[str] | None = None,
    last_columns: set[str] | None = None,
    id_columns: set[str] | None = None,
) -> None:
    first_columns = first_columns or set()
    last_columns = last_columns or set()
    id_columns = id_columns or set()

    identifier = _build_identifier_series(
        df,
        normalized_columns,
        full_columns=full_columns,
        first_columns=first_columns,
        last_columns=last_columns,
        id_columns=id_columns,
    )
    if identifier.dropna().empty:
        return

    alias_series = identifier.map(lambda value: _build_alias(prefix, value) if pd.notna(value) else pd.NA)
    alias_parts = alias_series.map(_split_alias)
    alias_first = alias_parts.map(lambda parts: parts[0] if parts else pd.NA)
    alias_last = alias_parts.map(lambda parts: parts[1] if parts else pd.NA)

    for raw_column, normalized_column in normalized_columns.items():
        if normalized_column in full_columns or normalized_column in id_columns:
            _ensure_string_compatible_column(df, raw_column)
            df.loc[identifier.notna(), raw_column] = alias_series[identifier.notna()]
        elif normalized_column in first_columns:
            _ensure_string_compatible_column(df, raw_column)
            df.loc[identifier.notna(), raw_column] = alias_first[identifier.notna()]
        elif normalized_column in last_columns:
            _ensure_string_compatible_column(df, raw_column)
            df.loc[identifier.notna(), raw_column] = alias_last[identifier.notna()]


def _build_alias(prefix: str, raw_value: str) -> str:
    digest = hashlib.sha1(str(raw_value).strip().lower().encode("utf-8")).hexdigest()[:6].upper()
    return f"{prefix} {digest}"


def _split_alias(alias: str | None) -> tuple[str, str] | None:
    if alias is None or pd.isna(alias):
        return None
    parts = str(alias).split(" ", 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _ensure_string_compatible_column(df: pd.DataFrame, column: str) -> None:
    if not pd.api.types.is_object_dtype(df[column]) and not pd.api.types.is_string_dtype(df[column]):
        df[column] = df[column].astype("object")


def _mask_high_risk_text_columns(
    df: pd.DataFrame,
    normalized_columns: dict[str, str],
) -> None:
    for raw_column, normalized_column in normalized_columns.items():
        if not pd.api.types.is_object_dtype(df[raw_column]) and not pd.api.types.is_string_dtype(df[raw_column]):
            continue

        placeholder = _placeholder_for_high_risk_column(normalized_column)
        if placeholder is None:
            continue

        mask = df[raw_column].notna() & (df[raw_column].astype(str).str.strip() != "")
        if mask.any():
            df.loc[mask, raw_column] = placeholder


def _placeholder_for_high_risk_column(normalized_column: str) -> str | None:
    if normalized_column in HIGH_RISK_EXACT_COLUMNS:
        if "instance" in normalized_column:
            return "Masked instance"
        return "Masked identifier list"

    tokens = set(normalized_column.split("_"))
    for required_tokens in HIGH_RISK_TEXT_TOKEN_SETS:
        if required_tokens.issubset(tokens):
            return "Masked text"

    return None


def _mask_dataset_specific_columns(
    df: pd.DataFrame,
    normalized_columns: dict[str, str],
    dataset_key: str | None,
) -> None:
    for raw_column, normalized_column in normalized_columns.items():
        if normalized_column in {"stage1_id_list", "instanceid"}:
            df[raw_column] = "Hidden"
        elif normalized_column == "learner_list":
            df[raw_column] = "Masked learner list"
        elif normalized_column == "learner_list_concat":
            df[raw_column] = "Masked learner list"
