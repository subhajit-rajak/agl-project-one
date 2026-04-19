package com.subhajitrajak.agl.network

import retrofit2.http.Body
import retrofit2.http.POST

data class DiagnosisRequest(
    val age: Float,
    val sex: String,
    val height_cm: Float,
    val weight_kg: Float,
    val symptoms_text: String
)

data class DiagnosisResponse(
    val disease: String? = null,
    val confidence: Double? = null,
    val risk_score: Double? = null,
    val risk_label: String? = null,
    val bmi: Double? = null,
    val description: String? = null,
    val precautions: List<String>? = null,
    val extracted_symptoms: List<String>? = null,
    val error: String? = null
)

interface ApiService {
    @POST("predict")
    suspend fun predictHealth(@Body request: DiagnosisRequest): DiagnosisResponse
}
