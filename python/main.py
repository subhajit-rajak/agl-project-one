from transformers import pipeline
import joblib
import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz
ner_pipe = pipeline(
    "ner",
    model="kechemale/eng-am-symptom-ner",
    tokenizer="kechemale/eng-am-symptom-ner",
    aggregation_strategy="first"
)
desc_df  = pd.read_csv("./symptom_Description.csv").fillna("")
prec_df  = pd.read_csv("./symptom_precaution.csv").fillna("")

desc_map = dict(zip(desc_df["Disease"], desc_df["Description"]))
 
prec_map = {}
for _, row in prec_df.iterrows():
    precs = [row[c].strip() for c in ["Precaution_1","Precaution_2",
                                       "Precaution_3","Precaution_4"]
             if str(row[c]).strip()]
    prec_map[row["Disease"]] = precs
 
 
def get_description(disease: str) -> str:
    """Fuzzy-tolerant description lookup."""
    if disease in desc_map:
        return desc_map[disease]
    # try case-insensitive
    for k, v in desc_map.items():
        if k.lower() == disease.lower():
            return v
    return "No description available."
 
 
def get_precautions(disease: str) -> list[str]:
    """Fuzzy-tolerant precaution lookup."""
    if disease in prec_map:
        return prec_map[disease]
    for k, v in prec_map.items():
        if k.lower() == disease.lower():
            return v
    return ["Consult a qualified medical professional."]
def extract_symptoms(text: str) -> list:
    """Extract symptom words from raw text using NER pipeline."""
    results = ner_pipe(text)
    symptoms = [entity["word"].strip() for entity in results]
    print(f"📌 Raw NER output: {symptoms}")
    return symptoms

#Predict Disease

def predict_disease(symptoms_present: list[str], top_n: int = 3) -> None:
    """
    Predict the most likely disease(s) from a list of symptom names.
 
    Parameters
    ----------
    symptoms_present : list of symptom strings exactly as they appear in the dataset
                       e.g. ["itching", "skin_rash", "nodal_skin_eruptions"]
    top_n            : how many top predictions to show (uses predict_proba)
    """
    model      = joblib.load("./models/disease_classifier/disease_classifier/disease_model.pkl")
    encoder    = joblib.load("./models/disease_classifier/disease_classifier/label_encoder.pkl")
    sym_cols   = joblib.load("./models/disease_classifier/disease_classifier/symptom_columns.pkl")
 
    # Build a zero-vector, then flip the present symptoms to 1
    input_vec = np.zeros(len(sym_cols), dtype=int)
    for sym in symptoms_present:
        sym = sym.strip()
        if sym in sym_cols:
            input_vec[sym_cols.index(sym)] = 1
        else:
            print(f"  ⚠  Unknown symptom ignored: '{sym}'")
 
    proba      = model.predict_proba([input_vec])[0]
    top_idx    = np.argsort(proba)[::-1][:top_n]
 
    print(f"\nSymptoms provided : {symptoms_present}")
    print(f"{'Rank':<5} {'Disease':<45} {'Confidence':>10}")
    print("─" * 62)
    for rank, idx in enumerate(top_idx, 1):
        disease = encoder.inverse_transform([idx])[0]
        print(f"{rank:<5} {disease:<45} {proba[idx]*100:>9.2f}%")
    best_idx        = top_idx[0]
    best_disease    = encoder.inverse_transform([best_idx])[0]
    best_confidence = round(float(proba[best_idx]) * 100, 2)
    return best_disease, best_confidence


RF_FEATURES = joblib.load("./models/disease_classifier/disease_classifier/symptom_columns.pkl")  # saved in disease_prediction.py
KNOWN_SYMPTOMS = list(RF_FEATURES)

from rapidfuzz import process, fuzz
import re

KNOWN_SYMPTOMS = list(RF_FEATURES)

SYNONYM_MAP = {
    "fever"           : "high_fever",
    "temperature"     : "high_fever",
    "runny nose"      : "runny_nose",
    "stomach ache"    : "stomach_pain",
    "belly ache"      : "belly_pain",
    "throwing up"     : "vomiting",
    "threw up"        : "vomiting",
    "can't breathe"   : "breathlessness",
    "short of breath" : "breathlessness",
    "tired"           : "fatigue",
    "tiredness"       : "fatigue",
    "no appetite"     : "loss_of_appetite",
    "loss of hunger"  : "loss_of_appetite",
    "yellow eyes"     : "yellowing_of_eyes",
    "yellow skin"     : "yellowish_skin",
    "sore throat"     : "throat_irritation",
    "body ache"       : "muscle_pain",
    "body pain"       : "muscle_pain",
}

def process_symptoms(raw_symptoms: list, threshold: int = 60) -> list:
    """Clean → Normalize → Synonym check → Fuzzy match, all in one step."""
    matched = []

    for s in raw_symptoms:
        # Step 1: Clean — remove punctuation, fix spacing
        cleaned = re.sub(r'[^\w\s]', '', s)       # remove . , ; etc
        cleaned = re.sub(r'\s+', ' ', cleaned)     # collapse spaces
        cleaned = cleaned.lower().strip()

        # Step 2: Synonym map check
        if cleaned in SYNONYM_MAP:
            matched.append(SYNONYM_MAP[cleaned])
            print(f"  📖 '{s}' → synonym → '{SYNONYM_MAP[cleaned]}'")
            continue

        # Step 3: Normalize — spaces to underscores
        norm = cleaned.replace(' ', '_')

        # Step 4: Fuzzy match against known symptoms
        result = process.extractOne(norm, KNOWN_SYMPTOMS, scorer=fuzz.token_sort_ratio)

        if result and result[1] >= threshold:
            matched.append(result[0])
            print(f"  ✅ '{s}' → '{result[0]}' (score: {result[1]})")
        else:
            print(f"  ⚠️  '{s}' → no match (best: {result[1] if result else 0})")

    return matched

def risk_label(score: float) -> str:
    """Convert numeric score to a human-readable risk band."""
    if score < 25:
        return "🟢 Low Risk"
    elif score < 50:
        return "🟡 Moderate Risk"
    elif score < 75:
        return "🟠 High Risk"
    else:
        return "🔴 Critical Risk"
 
 
def predict_risk(age: float,
                 sex: str,
                 height_cm: float,
                 weight_kg: float,
                 disease_name: str) -> dict:
    """
    Predict risk score for a patient.
 
    Parameters
    ----------
    age          : patient age in years
    sex          : "Male" or "Female"
    height_cm    : height in centimetres
    weight_kg    : weight in kilograms
    disease_name : disease exactly as in DISEASE_SEVERITY (or the predicted disease)
 
    Returns
    -------
    dict with risk_score (float), risk_label (str), bmi (float)
    """
    model_      = joblib.load("./models/disease_classifier/risk_evaluation/risk_model.pkl")
    encoder_    = joblib.load("./models/disease_classifier/risk_evaluation/risk_label_encoder.pkl")
    dis_list_   = joblib.load("./models/disease_classifier/risk_evaluation/risk_disease_list.pkl")
 
    # Encode inputs
    sex_enc = 1 if sex.strip().lower() == "male" else 0
    bmi     = weight_kg / ((height_cm / 100) ** 2)
 
    if disease_name in dis_list_:
        disease_enc = dis_list_.index(disease_name)
    else:
        # Unknown disease → use default severity midpoint
        print(f"  ⚠  '{disease_name}' not in catalogue. Using default severity.")
        disease_enc = 0
 
    features = np.array([[age, sex_enc, height_cm, weight_kg, bmi, disease_enc]])
    score    = float(np.clip(model_.predict(features)[0], 0, 100))
 
    result = {
        "risk_score" : round(score, 2),
        "risk_label" : risk_label(score),
        "bmi"        : round(bmi, 2),
    }
    return result
# sym = "I have fever, headache, and joint pain with chills , I also have diarrhoea , headache , vomiting and sweating"
# extract_1 = extract_symptoms(sym)
# processed_symptoms = process_symptoms(extract_1)
# disease , confidence = predict_disease(
#     processed_symptoms,
#     top_n=3
# )
# print("\n─── Demo Predictions ───\n")
# age = input("Enter patient age: ")
# sex = input("Enter patient sex (Male/Female): ")
# height = input("Enter patient height in cm: ")
# weight = input("Enter patient weight in kg: ")
# # test_cases = [ ... same ...]

# symptom_input = input("Enter symptoms :")
# extract_1 = extract_symptoms(symptom_input)
# processed_symptoms = process_symptoms(extract_1)
# disease , confidence = predict_disease(
#     processed_symptoms,
#     top_n=3
# )
# tc = {"age": int(age) if age else 20, "sex": sex, "height_cm": float(height) if height else 170, "weight_kg": float(weight) if weight else 70, "disease_name": disease}
# tc["disease_name"] = disease
# result = predict_risk(**tc)
# print(f"Patient : {tc['age']}y {tc['sex']}, {tc['height_cm']}cm, "
#         f"{tc['weight_kg']}kg → BMI {result['bmi']}")
# print(f"Disease : {tc['disease_name']}")
# print(f"Risk    : {result['risk_score']:.1f}/100  {result['risk_label']}")
# print("\n")
# print(f"The Confidence of the predicted disease is {confidence:.2f}%")
# print("\n")
# print(f"Description: {get_description(disease)}")
# print("\n")
# 
# for p in get_precautions(disease):
#     print(f"Precaution: {p}")
# print(f"  Precautions: {', '.join(get_precautions(disease))}")
# for tc in test_cases:
#     result = predict_risk(**tc)
#     print(f"  Patient : {tc['age']}y {tc['sex']}, {tc['height_cm']}cm, "
#           f"{tc['weight_kg']}kg → BMI {result['bmi']}")
#     print(f"  Disease : {tc['disease_name']}")
#     print(f"  Risk    : {result['risk_score']:.1f}/100  {result['risk_label']}")
#     print()
# print(KNOWN_SYMPTOMS)