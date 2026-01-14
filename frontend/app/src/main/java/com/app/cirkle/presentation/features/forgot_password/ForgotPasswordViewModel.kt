package com.app.cirkle.presentation.features.forgot_password

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.core.utils.validation.AuthInputValidator
import com.app.cirkle.data.model.auth.request.ForgotPasswordRequest
import com.app.cirkle.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ForgotPasswordViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<ForgotPasswordUiState>(ForgotPasswordUiState.Idle)
    val uiState: StateFlow<ForgotPasswordUiState> = _uiState.asStateFlow()

    fun resetPassword(userId: String, dob: String, newPassword: String) {
        // Basic validation
        if (userId.isBlank() || dob.isBlank() || newPassword.isBlank()) {
            _uiState.value = ForgotPasswordUiState.Error("All fields are required.")
            return
        }

        if(!AuthInputValidator.isValidUserId(userId)){
            _uiState.value= ForgotPasswordUiState.Error("Invalid User ID. It must be 2 uppercase letters followed by 5 digits.")
            return
        }

        if(!AuthInputValidator.isValidPassword(newPassword)){
            _uiState.value= ForgotPasswordUiState.Error("Invalid Password. It must be 8+ characters and include uppercase, lowercase, number, and special character.")
            return
        }

        _uiState.value = ForgotPasswordUiState.Loading
        viewModelScope.launch {
            val request = ForgotPasswordRequest(
                userId = userId,
                dateOfBirth = dob,
                newPassword = newPassword
            )
            authRepository.forgotPassword(request).collect { result ->
                _uiState.value = when (result) {
                    is ResultWrapper.Success -> ForgotPasswordUiState.Success("Password updated successfully")
                    is ResultWrapper.GenericError -> ForgotPasswordUiState.Error(result.error ?: "An unknown error occurred")
                    is ResultWrapper.NetworkError -> ForgotPasswordUiState.Error("Network error. Please check your connection.")
                }
            }
        }
    }
} 