import traceback
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)

stroke_model = joblib.load(BASE_DIR / "model.joblib")
print("Loaded model keys:", list(stroke_model.keys()))

# Map form values to the exact category strings the model was trained on
GENDER_MAP = {"Male": "Male", "Female": "Female"}
YES_NO_MAP = {"Yes": "Yes", "No": "No"}
BINARY_MAP = {"0": 0, "1": 1}
RESIDENCE_MAP = {"Urban": "Urban", "Rural": "Rural"}
WORK_TYPE_MAP = {
    "Private": "Private",
    "Self-employed": "Self-employed",
    "Government job": "Govt_job",
    "Children": "children",
    "Never Worked": "Never_worked",
}
SMOKING_MAP = {
    "Never Smoked": "never smoked",
    "Formerly Smoked": "formerly smoked",
    "Smokes": "smokes",
    "Unknown": "Unknown",
}


def parse_form(form):
    """Convert raw form data into a model-ready dict. Raises KeyError/ValueError on bad input."""
    return {
        "gender": GENDER_MAP[form["gender"]],
        "age": float(form["age"]),
        "hypertension": BINARY_MAP[form["hypertension"]],
        "heart_disease": BINARY_MAP[form["heart_disease"]],
        "ever_married": YES_NO_MAP[form["ever_married"]],
        "work_type": WORK_TYPE_MAP[form["work_type"]],
        "Residence_type": RESIDENCE_MAP[form["residence_type"]],
        "avg_glucose_level": float(form["avg_glucose_level"]),
        "bmi": float(form["bmi"]),
        "smoking_status": SMOKING_MAP[form["smoking_status"]],
    }


def predict_input(single_input):
    preprocessor = stroke_model["preprocessor"]
    input_df = pd.DataFrame([single_input])[list(preprocessor.feature_names_in_)]
    input_df["age"] = np.ceil(input_df["age"])

    encoded_cols = stroke_model["encoded_cols"]
    numerical_cols = stroke_model["numeric-cols"]
    input_df[encoded_cols] = preprocessor.transform(input_df)

    X = input_df[numerical_cols + encoded_cols]
    model = stroke_model["model"]
    return int(model.predict(X)[0]), float(model.predict_proba(X)[0, 1])


@app.route("/", methods=["GET", "POST"])
def index():
    error = None

    if request.method == "POST":
        print("Form data received:", dict(request.form))

        try:
            single_input = parse_form(request.form)
        except (KeyError, ValueError) as e:
            traceback.print_exc()
            error = f"Invalid input: {e}"
            return render_template("index.html", form=request.form, result=None, probability=None, error=error)

        prediction, proba = predict_input(single_input)
        result = "Likely" if prediction == 1 else "Not Likely"
        return render_template("result.html", result=result, probability=round(proba * 100, 1))

    return render_template("index.html", form=request.form, result=None, probability=None, error=error)


if __name__ == "__main__":
    app.run(debug=True)