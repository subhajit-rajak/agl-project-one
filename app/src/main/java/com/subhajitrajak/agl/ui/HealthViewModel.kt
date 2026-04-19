package com.subhajitrajak.agl.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.subhajitrajak.agl.network.DiagnosisRequest
import com.subhajitrajak.agl.network.DiagnosisResponse
import com.subhajitrajak.agl.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class UiState {
    object Idle : UiState()
    object Loading : UiState()
    data class Success(val data: DiagnosisResponse) : UiState()
    data class Error(val message: String) : UiState()
}

class HealthViewModel : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Idle)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    fun predictHealth(
        age: Float,
        sex: String,
        heightCm: Float,
        weightKg: Float,
        symptomsText: String
    ) {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            try {
                val request = DiagnosisRequest(age, sex, heightCm, weightKg, symptomsText)
                val response = RetrofitClient.apiService.predictHealth(request)
                
                if (response.error != null) {
                    _uiState.value = UiState.Error(response.error)
                } else {
                    _uiState.value = UiState.Success(response)
                }
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message ?: "An unexpected error occurred.")
            }
        }
    }

    fun reset() {
        _uiState.value = UiState.Idle
    }
}
