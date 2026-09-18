from flask import Flask, render_template, request, jsonify
from googletrans import Translator
import os
from PIL import Image 

app = Flask(__name__)

IMAGE_FOLDER = "static/hand_signs/"

def ensure_png_format():
    for filename in os.listdir(IMAGE_FOLDER):
        file_path = os.path.join(IMAGE_FOLDER, filename)
        if not filename.lower().endswith(".png"):
            try:
                base_name, _ = os.path.splitext(filename)
                new_file_path = os.path.join(IMAGE_FOLDER, f"{base_name}.png")
                img = Image.open(file_path)
                img.save(new_file_path, "PNG")
                os.remove(file_path)  
                print(f"Converted {filename} to PNG.")
            except Exception as e:
                print(f"Error converting {filename}: {e}")
                
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/recognize_speech", methods=["POST"])
def recognize_speech():
    try:
        ensure_png_format()

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

