package com.app.cirkle.presentation.common

sealed class Resource<out T> {
    object Idle:Resource<Nothing>()
    object Loading : Resource<Nothing>()
    data class Success<T>(val data: T) : Resource<T>()
    data class Error(val message: String) : Resource<Nothing>()
}
