import os
from pathlib import Path
from jinja2 import Environment
import json
from xhtml2pdf import pisa
import pymupdf
import re
from typing import Literal, Optional
from pydantic import BaseModel, ValidationError

# Type definition
class Question(BaseModel):
    """Define valid types for the question dictionaries."""
    type: Literal["text", "text_big", "checkbox", "dropdown", "listbox"]
    id: str
    prompt: str
    description: Optional[str] = None
    options: Optional[list[str]] = None
    selection: Optional[int] = None


# Primary class
class PDFFormulator():
    """Class used to organize and verify all data before generating the PDF."""
    # Key user-provided variables
    html_template: str
    question_list: list[Question]
    # Key generated variables
    html_rendered: str

    def __init__(self) -> None:
        """Runs on initializes and sets some variables"""
        # [x,y] pixel sizes for each field type
        self.field_sizes = {
            "text": [150,20],
            "text_big": [150,60],
            "checkbox": [20,20],
            "dropdown": [150,20],
            "listbox": [150,60]
        }
        # The indexes used for each field type (pymupdf)
        self.type_nos = {
            "text": 7,
            "text_big": 7,
            "checkbox": 2,
            "dropdown": 3,
            "listbox": 4
        }



    # Public methods 
    def set_field_size(self, type: Literal["text", "text_big", "checkbox", "dropdown", "listbox"], size: list[int]) -> None:
        """Provide the field 'type (exact string) and the size in [x,y] format for the size of that element type."""
        self.field_sizes[type] = size
    
    def get_field_size(self, type: Literal["text", "text_big", "checkbox", "dropdown", "listbox"]) -> list[int]:
        """Provide the field 'type' (exact string) and get the x/y size coords in an array of ints. Size is used by pymupdf to create the fields."""
        return self.field_sizes[type]

    def set_html_template_str(self, html_str: str) -> None:
        """Set the HTML template string to be used.
            Should be plain HTML or HTML with Jinga2."""
        if not isinstance(html_str, str):
            raise TypeError(f"Expected str, got {type(html_str).__name__}")
        self.html_template = html_str

    def set_question_list(self, provided_list: list[Question]) -> None:
        """Set the array of question dictionaries to be used.
            providedList should be an array of dictionaries or an array of Question types"""
        # Append ID if it is not present
        provided_list = self._enforce_ids(provided_list)
        # Confirm data is valid
        self._validate_question_list(provided_list)
        # Store array
        self.question_list = provided_list

    def output_form(self, path: str) -> None:
        """Creates the PDF document with fillable fields based on info provided."""
        # Render html from template then generate the pdf
        self.html_rendered: str = self._render_html()
        self._generate_pdf(path)
        # Modify the pdf to add fillable fields, replacing [[]] tags
        self._replace_placeholders(path)


    
    # Internal methods

    def _enforce_ids(self, question_list: list[Question]) -> list[Question]:
        """If an ID is not present for each question, this adds one based on prompt"""
        for question in question_list:
            if "id" not in question:
                starting_point = question["prompt"]
                no_whitespace = re.sub(r'\s+', '_', starting_point)
                no_spec_char = re.sub(r'[^\w]', '', no_whitespace)
                question["id"] = no_spec_char
        return question_list

    def _validate_question_list(self, question_list: list[Question]) -> None:
        """Validate that the current question_list has the correct keys. Takes a list. Returns nothing."""
        # Confirm the IDs are unique
        seen_ids = []
        for question in question_list:
            if question["id"] in seen_ids:
                raise Exception(f"The ID provided, '{question["id"]}', is used more than one. Correct this issue yourself by assigning a unique 'id' property.")
            else:
                seen_ids.append(question["id"])
        # Confirm the fields provided are valid (type check)
        try:
            question_list = [Question(**q) for q in question_list]
        except ValidationError as e:
            raise ValueError(f"The provided question data was invalid. Details: {e}")
    
    def _render_html(self) -> str:
        """Renders the html string by merging the template and the data. Returns the rendered html string."""
        env = Environment()
        template = env.from_string(self.html_template)
        return template.render(questions=self.question_list)
    
    def _generate_pdf(self, path: str) -> None:
        """Generates the PDF without the fillable field widgets, saving it to the provided path."""
        pisa.showLogging()
        with open(path, 'w+b') as file:
            # convert HTML to PDF
            pisa_status = pisa.CreatePDF(
                self.html_rendered, # page data
                dest=file,     # destination file
            )
            # Check for errors (dunno what to do with this yet)
            if not pisa_status:
                print("An error occurred while rendering!")
        
    def _replace_placeholders(self, path:str) -> None:
        """Locates the [[placeholder]] tags and replaces them with the relevant fillable field type."""
        # Load doc
        pdf = pymupdf.open('test.pdf')
        # Perform all steps on each page
        for page in pdf:
            # Create list of [[]] strings from page by searching all text
            all_text_on_page = page.get_text("text")
            located_tags = re.findall(r"(\[\[.*?\]\])", all_text_on_page)
            # Create list of rect coordinates for that text
            tag_locations = []
            for tag_text in located_tags:
                tag_locations.append(page.search_for(tag_text)[0])
            # Add a field then redact the tag text
            for i in range(len(tag_locations)):
                # The location and text for the field replacement
                tag = located_tags[i]
                rect = tag_locations[i]
                # Mark tag text for removal
                page.add_redact_annot(rect)
                # add new field
                self._add_widget(page, rect, tag)
            # Remove all redacted text from this page
            page.apply_redactions()
            pdf.saveIncr()
        # Unload doc
        pdf.close()

    def _add_widget(self, page, rect, tag: str) -> None:
        """Add a widget based on the tag and position"""
        # Determine field type and name:
        match = re.search(r'\[\[(\w+)\s+(\w+)\]\]', tag)
        tag_type = match.group(1)
        tag_name = match.group(2)
        # Locate the provided data based on the tag_name (id)
        question = next((item for item in self.question_list if item["id"] == tag_name), None)
        # Determine size of box
        ul = rect.top_left
        field_rect = pymupdf.Rect(
            ul.x,
            ul.y,
            ul.x + self.field_sizes[tag_type][0],
            ul.y + self.field_sizes[tag_type][1]
        )
        # Initializethe widget (standard fields)
        wgt = pymupdf.Widget()
        wgt.field_name = tag_name
        wgt.rect = field_rect
        wgt.field_type = self.type_nos[tag_type]
        if tag_type == "dropdown":
            wgt.choice_values = question.get("options", [])
        # Listbox specific settings/overrides
        if tag_type == "listbox":
            wgt.field_flags = pymupdf.PDF_CH_FIELD_IS_MULTI_SELECT
            wgt.choice_values = question.get("options", [])
        # Add widget to page
        page.add_widget(wgt)
            



