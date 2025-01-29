import pandas as pd
import re

def create_letter_tracker(df, export_csv=True, output_path="Letter Tracker.csv"):
    final_order = [
        'a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p',
        's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
        'g', 't', 'q', 'r', 'c', 'j'
    ]
    learner_info_cols = [
        "name_ta_rep", "school_rep", "learner_id", "class", "name_first_learner", "name_second_learner", "letters_correct", "group"
    ]
    learner_info_df = (
        df[learner_info_cols]
        .drop_duplicates(subset=["learner_id"])
        .copy()
    )
    letter_cols = [col for col in df.columns if re.match(r"^letters_.*_\d+$", col)]
    long_df = df.melt(
        id_vars=learner_info_cols,
        value_vars=letter_cols,
        var_name="letter_column",
        value_name="letter_val"
    )

    def parse_letter_info(col_name):
        parts = col_name.split("_")
        if len(parts) < 3:
            return pd.NA, pd.NA
        return parts[1], parts[2]

    long_df["parsed_letter"], long_df["parsed_index"] = zip(
        *long_df["letter_column"].apply(parse_letter_info)
    )
    long_df["letter_lower"] = long_df["parsed_letter"].str.lower()

    def letter_is_known(group):
        vals = group["letter_val"].dropna()
        if len(vals) == 0:
            return 0
        if (vals == '0').any():
            return 0
        if (vals == 'X').any():
            return 1
        return 0

    knowledge_df = (
        long_df
        .groupby(["learner_id", "letter_lower"])
        .apply(letter_is_known)
        .reset_index(name="knows_letter")
    )

    wide_df = knowledge_df.pivot(
        index="learner_id",
        columns="letter_lower",
        values="knows_letter"
    ).fillna(0)
    wide_df = wide_df.reindex(columns=final_order, fill_value=0)
    wide_df.reset_index(inplace=True)

    final_df = pd.merge(
        learner_info_df,
        wide_df,
        on="learner_id",
        how="left"
    )

    demo_cols = learner_info_cols
    letter_cols_final = final_order
    final_columns = demo_cols + letter_cols_final

    final_columns_unique = []
    seen = set()
    for col in final_columns:
        if col not in seen:
            final_columns_unique.append(col)
            seen.add(col)

    final_df = final_df[final_columns_unique]

    if export_csv:
        final_df.to_csv(output_path, index=False)

    return final_df
