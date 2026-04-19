from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import main as ml_logic

app = FastAPI(title="AGL Health API")

class DiagnosisRequest(BaseModel):
    age: float
    sex: str
    height_cm: float
    weight_kg: float
    symptoms_text: str

@app.post("/predict")
def predict_health(request: DiagnosisRequest):
    try:
        # 1. Extract symptoms from raw text using HuggingFace NER
        extracted_symptoms = ml_logic.extract_symptoms(request.symptoms_text)
        if not extracted_symptoms:
            return {"error": "Could not extract any recognizable symptoms. Please describe how you're feeling in more detail."}
            
        # 2. Process and map to known standard symptoms
        processed_symptoms = ml_logic.process_symptoms(extracted_symptoms)
        if not processed_symptoms:
            return {"error": "Could not map extracted symptoms to known catalogue. Please try using different terminology."}
            
        # 3. Predict disease from processed symptoms
        disease, confidence = ml_logic.predict_disease(processed_symptoms, top_n=3)
        
        # 4. Evaluate personalized risk given the disease
        risk_result = ml_logic.predict_risk(
            age=request.age,
            sex=request.sex,
            height_cm=request.height_cm,
            weight_kg=request.weight_kg,
            disease_name=disease
        )
        
        # 5. Fetch disease information
        description = ml_logic.get_description(disease)
        precautions = ml_logic.get_precautions(disease)
        
        return {
            "disease": disease,
            "confidence": confidence,
            "risk_score": risk_result["risk_score"],
            "risk_label": risk_result["risk_label"],
            "bmi": risk_result["bmi"],
            "description": description,
            "precautions": precautions,
            "extracted_symptoms": processed_symptoms
        }
    except Exception as e:
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
