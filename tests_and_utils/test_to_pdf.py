import os
import pdfkit

input_folder = "html_reports"
output_folder = "pdf_trackers"

# Common options to specify layout/size
options = {
    'orientation': 'Landscape',
    'page-size': 'A4',
    # If you want to remove margins so you can squeeze more content in:
    'margin-top': '0.25in',
    'margin-bottom': '0.25in',
    'margin-left': '0.25in',
    'margin-right': '0.25in',
}

for filename in os.listdir(input_folder):
    if filename.lower().endswith(".html"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(
            output_folder, os.path.splitext(filename)[0] + ".pdf"
        )

        # Pass the 'options' dictionary to pdfkit
        pdfkit.from_file(input_path, output_path, options=options)

        print(f"Converted {filename} to PDF (landscape) at {output_path}")
