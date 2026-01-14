package com.app.cirkle.presentation.features.register

sealed class RegisterViewState{
    object Loading: RegisterViewState()
    object Idle: RegisterViewState()
    object Success: RegisterViewState()
    data class Error(val message:String): RegisterViewState()
}