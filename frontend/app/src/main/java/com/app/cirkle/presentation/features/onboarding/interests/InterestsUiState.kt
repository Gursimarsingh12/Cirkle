package com.app.cirkle.presentation.features.onboarding.interests

import com.app.cirkle.domain.model.user.Interest

sealed class InterestsUiState {
    object Loading : InterestsUiState()
    data class Success(val interests: List<Interest>) : InterestsUiState()
    object UpdateComplete : InterestsUiState()
    data class Error(val message: String) : InterestsUiState()
    object Idle: InterestsUiState()
}