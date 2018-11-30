import pdfkit
import os
class PDFGenerator:

    def __init__(self, outfile):
        self.output_pdf = outfile
        self.content = ""

    def generate_table(self, data, headers, title, explanation=None):
        rows = []
        for row in data:
            rows.append(''.join(['<td scope="col">' + str(h) + '</td>' for h in row]))


        template = f"""
        <div class="row">
            <div class="col-xs-12">
                {self.create_header(title, 3)}
                <table class="table table-striped">
                    <caption>
                        {''.join([f'{(index+1) * "*"}{("&nbsp"*(len(explanation) - index)).replace("-", " ")}{cap}<br>' for index, cap in enumerate(explanation)])}
                    </caption>
                    <thead>
                        <tr>
                            {''.join(['<th scope="col">' + str(h) + '</th>' for h in headers])}
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(['<tr>' + str(r) + '</tr>' for r in rows])}
                    </tbody>
                    </table>
                </div>
            </div>
            """
        return template

    def add_readonly_field(self, label, text):
        field = f"""
            <form class="form-inline">
                <div class="form-group row">
                    <label for="{label}" class="col-sm-2 col-form-label"><strong>{label}</strong></label>
                    <div class="col-sm-10">
                        <input type="text" readonly class="form-control-plaintext" id="{label}" value="{text}">
                    </div>
                </div>
            </form>
        """
        self.add_content(field)

    def add_content(self, content):
        self.content += content

    def create_header(self, title, header_type: int=1):
        return f'<h{header_type} class="text-center">{title}</h{header_type}>'

    def add_header(self, title, header_type: int=1):
        self.add_content(self.create_header(title, header_type))

    def add_space(self, space):
        self.add_content(f'<div style="height: {space}px;"></div>')

    def generate_pdf(self):
        print("Generating PDF")
        pdf = f"""
        <!doctype html>
        <html>

            <head>
                <title>Test results</title>
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
            </head>

            <body>
                <div class="container-fluid">
                    {self.content}
                </div>
            </body>
        </html>
        """
        pdfkit.from_string(pdf, self.output_pdf)

if __name__ == "__main__":
    generator = PDFGenerator("out.pdf")
    table = generator.generate_table(
        [[1,2,3],[4,5,6], [7,8,9]],
        ["One", "Two", "Tree"],
        "Status code",
        "Explain")
    generator.add_header("10 requests in parallel")
    generator.add_content(table)
    generator.generate_pdf()