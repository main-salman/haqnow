import os
import weasyprint

for txt_file in os.listdir('.'):
    if txt_file.endswith('.txt'):
        with open(txt_file, 'r') as f:
            content = f.read()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #d32f2f; }}
                h2 {{ color: #1976d2; }}
                pre {{ white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <pre>{content}</pre>
        </body>
        </html>
        """
        
        pdf_file = txt_file.replace('.txt', '.pdf')
        weasyprint.HTML(string=html_content).write_pdf(pdf_file)
        print(f'Created {pdf_file}')
