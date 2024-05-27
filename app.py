from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import pytesseract
from PIL import Image
import cv2
import numpy as np
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/'
VISUAL_FOLDER = 'static/visuals/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VISUAL_FOLDER'] = VISUAL_FOLDER


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return render_template('index.html', uploaded=True, image_url=filepath)


@app.route('/extract', methods=['POST'])
def extract_file():
    image_path = request.form['image_path']
    if not image_path:
        return 'No image uploaded'
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)

    # Process the image to extract visual elements
    visual_paths = process_image(image_path)

    return render_template('result.html', image_url=image_path, text=text, visual_paths=visual_paths)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/visuals/<filename>')
def visual_file(filename):
    return send_from_directory(app.config['VISUAL_FOLDER'], filename)


def process_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    visual_paths = []

    for i, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        if w > 50 and h > 50:  # filter out small noise
            visual = image[y:y + h, x:x + w]
            visual_path = os.path.join(app.config['VISUAL_FOLDER'], f'visual_{i}.png')
            cv2.imwrite(visual_path, visual)
            visual_paths.append(visual_path)

    return visual_paths


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(VISUAL_FOLDER):
        os.makedirs(VISUAL_FOLDER)
    app.run(debug=True, host='192.168.137.147');
