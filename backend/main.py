import cv2
import numpy as np
import imutils
from flask import Flask, request, jsonify

# Initialize the Flask application
app = Flask(__name__)

# --- OMR Processing Logic encapsulated in a function ---


def process_omr(image_bytes):
    """
    Processes an OMR sheet image from bytes and returns the score.
    Raises ValueError for processing errors.
    """
    # 1. Decode the image from bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError(
            "Image data could not be decoded. The file may be corrupt or not a valid image.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # 2. Find contours (the bubbles)
    cnts = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    questionCnts = []
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        if w >= 20 and h >= 20 and 0.9 <= ar <= 1.2:  # Filter for circular shapes
            questionCnts.append(c)

    # Sanity check: Ensure bubbles were found
    if len(questionCnts) == 0:
        raise ValueError(
            "No bubbles were recognized in the image. Please ensure the image is clear and well-lit.")

    # Sanity check: Ensure we have a complete set of questions (4 options each)
    if len(questionCnts) % 4 != 0:
        raise ValueError(
            f"An incomplete number of bubbles ({len(questionCnts)}) was detected. Grading cannot proceed.")

    # Sort the bubbles top-to-bottom
    questionCnts = sorted(questionCnts, key=lambda c: cv2.boundingRect(c)[1])

    # 3. Define the Answer Key
    # (question index: correct option index)
    answer_key = {0: 1, 1: 2, 2: 2, 3: 3, 4: 1}

    # 4. Grade the questions
    score = 0
    total_questions = len(answer_key)

    # Iterate over questions in chunks of 4 bubbles
    for (q_idx, i) in enumerate(range(0, len(questionCnts), 4)):
        # Sort bubbles for the current question left-to-right
        cnts = sorted(questionCnts[i:i + 4],
                      key=lambda c: cv2.boundingRect(c)[0])
        bubbled = None

        # Find the bubbled answer
        for (j, c) in enumerate(cnts):
            mask = np.zeros(thresh.shape, dtype="uint8")
            cv2.drawContours(mask, [c], -1, 255, -1)
            mask = cv2.bitwise_and(thresh, thresh, mask=mask)
            total = cv2.countNonZero(mask)

            if bubbled is None or total > bubbled[0]:
                bubbled = (total, j)

        # Check if an answer was bubbled and compare to the key
        # We can add a threshold to ensure the bubble is substantially filled
        # Example threshold: more than 200 pixels filled
        if bubbled and bubbled[0] > 200:
            correct_answer_idx = answer_key.get(q_idx)
            if correct_answer_idx == bubbled[1]:
                score += 1

    return score, total_questions


# --- API Endpoint Definition ---
@app.route('/grade', methods=['POST'])
def grade_sheet():
    """
    API endpoint to grade an OMR sheet image.
    Expects a multipart/form-data request with an image file under the key 'file'.
    """
    # Check if a file was sent
    if 'file' not in request.files:
        return jsonify({
            "status": "error",
            "message": "No image file provided. Please upload a file with the key 'file'."
        }), 400

    file = request.files['file']

    # Check if the filename is empty (no file selected)
    if file.filename == '':
        return jsonify({
            "status": "error",
            "message": "No file selected."
        }), 400

    try:
        # Read the image file bytes
        image_bytes = file.read()

        # Process the OMR sheet
        score, total_questions = process_omr(image_bytes)

        # Return successful result
        return jsonify({
            "status": "success",
            "score": score,
            "total_questions": total_questions
        }), 200

    except ValueError as e:
        # Handle specific errors from the processing logic (e.g., unclear image)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

    except Exception as e:
        # Handle unexpected backend issues
        # Log the error for debugging
        print(f"An unexpected error occurred: {e}")
        return jsonify({
            "status": "error",
            "message": "An internal server error occurred. Please try again later."
        }), 500


# --- Run the Flask App ---
if __name__ == '__main__':
    # Use host='0.0.0.0' to make the app accessible on your local network
    app.run(host='0.0.0.0', port=5000, debug=True)
