# PDF-Formulator
A Python module that combines jinja2, xhtml2pdf, and pymupdf. Provide a an array of questions and an jinja HTML template and it will be converted into a PDF form with fillable fields.

# How to install

`pip install pdf-formulator`

# Usage

## The data

First, supply an array of dictionaries with the following keys:

| key | required? | description |
|--|--|--|
| type | yes | The "type" of field used. Valid options are: "text", "text_big", "checkbox", "dropdown", "listbox" |
| prompt | yes | The question being asked. String. |
| description | no | Additional explanation to clarify the prompt. String. |
| options | * | The selection options. Required only for dropdown or listbox. Array of strings. |
| id | no | A unique identifier for the field. String. By default, an ID is made up using the prompt if one is not provided, but it is good practice to manually set it.

An example:
```
    [
        {
            "type": "text",
            "prompt": "What is your name?",
            "description": "Provide your name, please."
        },
        {
            "type": "big_text",
            "prompt": "What do you think is neat?"
        },
        {
            "type": "checkbox",
            "prompt": "Are you having a good day?",
            "description": "Check the box if your day is going well. Sometimes a description might go for a long time as well so there needs to be handling for that."
        },
        {
            "type": "dropdown",
            "prompt": "What weekday is it?",
            "options": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday"
            ]
        },
        {
            "type": "listbox",
            "prompt": "Pick your favorite days.",
            "description": "You can hold Ctrl when clicking to select more than one.",
            "options": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday"
            ]
        }
    ]
```

## The template
An HTML string is required. It will use jinja2 to render the template, then that will be generated into a PDF using xhtml2pdf.

**Note:** xhtml2pdf has very limited CSS! You have to work within the limitations.

Example template:
```
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Sample Form</title>
    <style>
        /* Footer and page dimensions */
        @page {
            size: letter;
            margin: 1cm;           
            @frame footer_frame {
                -pdf-frame-content: footer_content;
                left: 50pt; width: 512pt; top: 772pt; height: 20pt;
            }
        }
        .footer {
            text-align: right;
            vertical-align: bottom;
        }

        /* Question table and left-bar styling */
        table {
            margin-bottom: 10px;
            background-color: #ececec;
            -pdf-outline: true;
        }
        td.sidebar {
            padding: 0px;
            width: 3px;
            background-color: black;
        }
        /* The left/right cells where question/description and input fields go (respectively) */
        td.left{
            margin: 4px;
            padding: 8px;
            vertical-align: top;
        }
        td.right {
            margin: 4px;
            padding: 3px 2px 2px 2px;
            border-left: 0px;
            vertical-align: top;
            width: 220px;
        }

        /* Text formatting */
        div {
            padding: 4px;
            margin: 0px;
            line-height: normal
        }
        div.prompt {
            font-size: 14px;
        }
        div.description {
            font-size: 10px;
        }
        div.widget {
            font-size: 4px;
        }

        .height-taller {
            height: 92px;
        }
    </style>
</head>
<body>
    <!-- FOOTER -->
    <div id="footer_content">
        <p class="footer">page <pdf:pagenumber> of <pdf:pagecount></p>
    </div>


    <div class="form-container">
        <h1>Questions Form</h1>
        

        {% if questions %}
            {% for item in questions %}


                <table class="vert-norm">
                    <tr>
                        {# LEFT SIDEBAR and height adjustment #}
                        <td class="sidebar{% if item.type == 'listbox' or item.type == 'text_big' %} height-taller{% endif %}">
                        </td>
                        {# LEFT CELL #}
                        <td class="left">
                            <div class="prompt">{{ item.prompt }}</div>
                                {% if item.description %}
                                    <div class="description">{{ item.description }}</div>
                                {% endif %}
                            </td>
                        {# RIGHT CELL #}
                        <td class="right">
                            <div class="widget">[[{{ item.type }} {{ item.id}}]]</div>
                        </td>
                    </tr>
                </table>


        
            {% endfor %}
        {% else %}
            <p style="text-align: center; color: #999;">No questions to display.</p>
        {% endif %}
    </div>
</body>
</html>
```

## Generating the form
Once you have the array of dictionaries (json_data) and the html string (html_str), you can generate the PDF.

```
form = PDFFormulator()
form.set_html_template_str(html_str)
form.set_question_list(json_data)
form.output_form("test.pdf")
```

## Other functions

| Command | Description |
| -- | -- |
| get_field_size | Provides the sizing for the given type (text, checkbox, etc) in the `[x,y]` format.
| set_field_size | Sets the size of the given type.


# Important notes
* This is a very clunky workaround. A proper solution would handle the PDF generation directly and lay out space automatically in the HTML to ensure fields always fit. As it is, it takes a lot of tweaking to get things laid out acceptably.
* I intend to iterate on this design and make improvements if my schedule allows. As-is, this was a solution to a problem, but I'd like to see something like this available at no cost. I could only find paid services/libraries that do it currently.