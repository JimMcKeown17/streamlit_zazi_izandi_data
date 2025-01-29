import pandas as pd

def assign_groups_by_cohort(df, group_size=7):
    """
    Assign groups within each cohort defined by 'school_rep' and 'class'.
    Groups are assigned based on sorting by 'surname' and 'letters_correct'.
    """
    # Sort by cohort, then by surname and letters_correct
    df = df.sort_values(by=['school_rep', 'class', 'letters_correct','name_second_learner']).reset_index(drop=True)

    # Define a grouping function for each cohort
    def assign_groups(group):
        group = group.reset_index(drop=True)
        group.index = group.index + 1  # Start index at 1
        group['group'] = (group.index - 1) // group_size + 1

        # Adjust the last group if necessary
        last_group = group['group'].max()
        last_group_count = group[group['group'] == last_group].shape[0]

        if last_group_count == 1 and last_group > 1:
            group.loc[group['group'] == last_group, 'group'] = last_group - 1
        elif last_group_count == 2 and last_group > 1:
            second_to_last_group_first_index = group[group['group'] == (last_group - 1)].index[0]
            group.loc[second_to_last_group_first_index, 'group'] = last_group - 2
            group.loc[group['group'] == last_group, 'group'] = last_group - 1
        elif last_group_count == 3 and last_group > 1:
            second_to_last_group_7th_index = group[group['group'] == (last_group - 1)].index[6]
            second_to_last_group_6th_index = group[group['group'] == (last_group - 1)].index[5]
            group.loc[second_to_last_group_7th_index, 'group'] = last_group
            group.loc[second_to_last_group_6th_index, 'group'] = last_group
        elif last_group_count == 4 and last_group > 1:
            second_to_last_group_7th_index = group[group['group'] == (last_group - 1)].index[6]
            group.loc[second_to_last_group_7th_index, 'group'] = last_group

        return group

    # Apply the grouping logic to each cohort
    df = df.groupby(['school_rep', 'class'], group_keys=False).apply(assign_groups)

    return df
