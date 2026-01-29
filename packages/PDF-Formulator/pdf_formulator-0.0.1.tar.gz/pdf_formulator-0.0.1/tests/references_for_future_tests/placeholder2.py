# During development, look at project root; in production, use a config path
TEMPLATE_DIR = Path(__file__).parent.parent.parent / 'templates'
JSON_DIR = Path(__file__).parent.parent.parent / 'test/json'

# Get HTML as str
with open(TEMPLATE_DIR / 'sample.html', 'r') as file:
    html_str = file.read()

# Get sample data
with open(JSON_DIR / 'questions.json', 'r') as file:
    json_data = json.load(file)

form = PDFFormulator()
form.set_html_template_str(html_str)
form.set_question_list(json_data)
form.output_form("test.pdf")