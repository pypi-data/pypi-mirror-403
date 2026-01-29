###############################
# DEV START
###############################

# During development, look at project root; in production, use a config path
TEMPLATE_DIR = Path(__file__).parent.parent.parent / 'templates'
JSON_DIR = Path(__file__).parent.parent.parent / 'test/json'

# Get HTML as str
with open(TEMPLATE_DIR / 'sample.html', 'r') as file:
    html_str = file.read()

# Get sample data
with open(JSON_DIR / 'questions.json', 'r') as file:
    json_data = json.load(file)

# Render html string from template
env = Environment(loader = FileSystemLoader(TEMPLATE_DIR))
template = env.get_template('sample.html')
rendered_html = template.render(questions=json_data)

# Render HTML to PDF
pisa.showLogging()
with open('test.pdf', 'w+b') as file:
    # convert HTML to PDF
    pisa_status = pisa.CreatePDF(
        rendered_html, # page data
        dest=file,     # destination file
    )
    # Check for errors
    if not pisa_status:
        print("An error occurred!")

# Load PDF and search for ANSWERGOHERE
pdf = pymupdf.open('test.pdf')
#text_instances = pdf.search_page_for(0,"ANSWERGOHERE")
all_text = pdf[0].get_text("text")
located_text = re.findall(r"(\[\[.*?\]\])", all_text)
text_instances = []
for text in located_text:
    text_instances.append(pdf[0].search_for(text)[0])

page = pdf[0]
i = 0
for rect in text_instances:
    i += 1
    # positioning and size
    point = rect.top_left
    rect = pymupdf.Rect(point.x, point.y, point.x+200, point.y+20)

    # mark old text for removal
    page.add_redact_annot(rect)
    # add new field
    wgt = pymupdf.Widget()
    wgt.field_name = f"field_{i}"
    wgt.rect = rect
    wgt.field_type = 7
    page.add_widget(wgt)


page.apply_redactions()
pdf.saveIncr()
pdf.close()


###############################
# DEV END
###############################