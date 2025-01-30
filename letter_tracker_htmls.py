import pandas as pd
import os


def create_styled_html(df):
    # Define the CSS styles
    styles = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            font-family: Arial, sans-serif;
            font-size: 8px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 4px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        thead {
            display: table-header-group; /* This ensures header repeats */
        }
        tfoot {
            display: table-footer-group; /* If you have a table footer */
        }
        .highlight {
            background-color: #FFEB3B;  /* Yellow background */
            font-weight: bold;
            text-align: center;
        }
        .blank {
            background-color: #ffffff;  /* White background */
        }
    </style>
    """

    # List of letter columns
    letter_cols = [
        'a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p', 's', 'h',
        'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x', 'g', 't', 'q', 'r', 'c', 'j'
    ]

    # Function to style cells based on value
    def style_cell(val, col):
        if col in letter_cols:
            if val == 1:
                return 'highlight'
            elif val == 0:
                return 'blank'
        return ''

    # Build the THEAD (header row)
    header_html = "<thead><tr>"
    for col in df.columns:
        header_html += f"<th>{col}</th>"
    header_html += "</tr></thead>"

    # Build the TBODY (data rows)
    data_rows_html = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            value = row[col]
            style_class = style_cell(value, col)
            # For letter columns, replace 1 with 'X' and 0 with blank
            if col in letter_cols:
                display_value = 'X' if value == 1 else ''
            else:
                display_value = value
            cells.append(f'<td class="{style_class}">{display_value}</td>')
        data_rows_html.append('<tr>' + ''.join(cells) + '</tr>')

    tbody_html = f"<tbody>{''.join(data_rows_html)}</tbody>"

    # Combine to form the full table
    table_html = f"<table>{header_html}{tbody_html}</table>"

    return styles + table_html

def main():
    # Read the CSV data
    df = pd.read_csv('Letter Tracker.csv')

    # Remove learner_id column and rename letters_correct
    df = df.drop('learner_id', axis=1)
    df = df.rename(columns={'letters_correct': 'EGRA_score',
                            'school_rep': 'School',
                            'name_first_learner': 'FName',
                            'name_second_learner': 'Surname'})

    # Create output directory if it doesn't exist
    os.makedirs('html_reports', exist_ok=True)

    # Generate a report for each teaching assistant
    for ta_name in df['name_ta_rep'].unique():
        # Filter data for this TA
        ta_df = df[df['name_ta_rep'] == ta_name]

        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Report for {ta_name}</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <h1>Letter Recognition Report for {ta_name}</h1>
            {create_styled_html(ta_df)}
        </body>
        </html>
        """

        # Save to file
        filename = f"html_reports/{ta_name.replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Generated report for {ta_name}")


if __name__ == "__main__":
    main()