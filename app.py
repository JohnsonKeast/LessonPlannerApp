from flask import Flask, render_template, request, jsonify, send_file
from openai import OpenAI
import os
from dotenv import load_dotenv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import logging

# Load environment variables from .env file in this case the api key from openai
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
)

app = Flask(__name__)

# Set up logging to capture errors
logging.basicConfig(level=logging.INFO)

# HTML template used for user input and generation of lesson plan results from json
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        subject = data.get('subject')
        year_level = data.get('year_level')
        lesson_topic = data.get('lesson_topic')
        weeks = data.get('weeks')
        keywords = data.get('keywords')

        prompt = (f"Using the New Zealand Curriculum, generate a detailed lesson plan for the subject '{subject}' "
                  f"targeted at year level '{year_level}'. The lesson topic is '{lesson_topic}'. Include objectives, "
                  f"materials such as videos or links, activities, and assessment methods. The lesson plan should cover "
                  f"{weeks} weeks and incorporate the following keywords: {keywords}. Ensure that the plan aligns with "
                  f"the curriculum's focus on key competencies, learning areas, and achievement objectives.")

        logging.info(f"Generated prompt: {prompt}")

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for generating lesson plans."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        lesson_plan = response.choices[0].message.content
        logging.info("Lesson plan generated successfully")
        return jsonify({'lesson_plan': lesson_plan})
    except Exception as e:
        logging.error(f"Error in generate endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        lesson_plan = request.json.get('lesson_plan')

        if not lesson_plan:
            error_message = 'No lesson plan provided'
            logging.warning(error_message)
            return jsonify({'error': error_message}), 400

        # Create a BytesIO object to hold the PDF data
        buffer = BytesIO()

        # Create a PDF with reportlab
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Add text to the PDF
        text_object = c.beginText(40, height - 40)
        text_object.setFont("Helvetica", 12)
        text_object.setTextOrigin(40, height - 40)
        text_object.textLines(lesson_plan)
        c.drawText(text_object)

        c.showPage()
        c.save()

        # Seek to the beginning of the BytesIO buffer
        buffer.seek(0)

        logging.info("PDF generated successfully")
        return send_file(
            buffer,
            as_attachment=True,
            download_name='lesson_plan.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        logging.error(f"Error in download endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run
