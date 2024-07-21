import pandas as pd

def process_zz_data_23(endline, sessions):
    endline = pd.merge(endline, sessions[['Mcode', 'Total No. of sessions','Total Sessions Through Oct' ]], on="Mcode")
    letter_cols = ['a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p', 's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
                   'g', 't', 'q', 'r', 'c', 'j']

    endline['Letters Known Endline'] = endline[letter_cols].notna().sum(axis=1)

    mask_end_mid = endline['Masi Letters Known Midline'].notna()
    mask_end = endline['Masi Letters Known Endline'].notna()

    endline.loc[mask_end, 'Letters Learned Endline'] = endline.loc[mask_end, 'Masi Letters Known Endline'] - \
                                                       endline.loc[mask_end, 'Masi Letters Known Baseline']
    endline.loc[mask_end_mid, 'Masi Letters Learned Midline'] = endline.loc[
                                                                    mask_end_mid, 'Masi Letters Known Midline'] - \
                                                                endline.loc[mask_end_mid, 'Masi Letters Known Baseline']
    mask_egra_endline = endline['Masi Egra Full Endline'].notna()

    endline.loc[mask_egra_endline, 'Egra Improvement Endline'] = endline.loc[
                                                                     mask_egra_endline, 'Masi Egra Full Endline'] - \
                                                                 endline.loc[
                                                                     mask_egra_endline, 'Masi Egra Full Baseline']
    mask_egra_mid_endline = endline['Masi Egra Full Midline'].notna()
    endline.loc[mask_egra_mid_endline, 'Egra Improvement Midline'] = endline.loc[mask_egra_mid_endline, 'Masi Egra Full Midline'] - \
                                                         endline.loc[mask_egra_mid_endline, 'Masi Egra Full Baseline']

    endline['List of Letters Known'] = endline[letter_cols].apply(
        lambda row: [letter for letter, value in row.items() if pd.notna(value)], axis=1)

    return endline