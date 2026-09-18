from flask import Flask, render_template, request, jsonify
from googletrans import Translator
import os

app = Flask(__name__)

IMAGE_FOLDER = "static/hand_signs/"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/recognize_speech", methods=["POST"])
def recognize_speech():
    try:
        data = request.get_json()
        text = data.get("text")
        lang = data.get("lang")

        if not text:
            return jsonify({"error": "No text provided!"}), 400

        if lang in ['hi', 'mr']:
            translator = Translator()
            translated_text = translator.translate(text, src=lang, dest='en').text
        else:
            translated_text = text

        images = []
        for letter in translated_text.upper():
            if letter == " ":
                images.append("__SPACE__")  # word-boundary marker for the frontend
            elif letter.isalpha():
                image_path = os.path.join(IMAGE_FOLDER, f"{letter}.png")
                if os.path.exists(image_path):
                    images.append(f"/{image_path}")
                else:
                    images.append(f"/static/hand_signs/missing.png")

        return jsonify({"text": text, "translated_text": translated_text, "images": images})

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
