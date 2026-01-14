package com.app.cirkle.presentation.features.login

sealed class LoginViewState {
    object Idle : LoginViewState()
    object Loading : LoginViewState()
    object Success : LoginViewState()
    data class Error(val message: String) : LoginViewState()
}