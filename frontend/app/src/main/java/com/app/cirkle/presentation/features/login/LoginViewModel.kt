package com.app.cirkle.presentation.features.login


import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.domain.repository.AuthRepository
import com.app.cirkle.core.utils.validation.AuthInputValidator
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.presentation.common.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class LoginViewModel @Inject constructor(private val repository: AuthRepository) : ViewModel() {

    private val _viewState = MutableStateFlow<Resource<Unit>>(Resource.Idle)
    val viewState: StateFlow<Resource<Unit>> = _viewState.asStateFlow()

    fun login(userId: String, password: String) {
        if (!validateInputs(userId, password)) {
            _viewState.value = Resource.Error("Invalid inputs")
            return
        }

        viewModelScope.launch {
            _viewState.value = Resource.Loading
            repository.login(userId, password).collect { result ->
                _viewState.value = when (result) {
                    is ResultWrapper.Success -> Resource.Success(Unit)
                    is ResultWrapper.GenericError -> {
                        val errorMessage = result.error ?: "An unknown error occurred"
                        Resource.Error(errorMessage)
                    }
                    is ResultWrapper.NetworkError -> Resource.Error("Network error occurred. Please check your connection.")
                }
            }
        }
    }

    private fun validateInputs(userId: String, password: String): Boolean {
        return AuthInputValidator.isValidUserId(userId) && AuthInputValidator.isValidPassword(password)
    }
}
