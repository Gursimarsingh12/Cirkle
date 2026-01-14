package com.app.cirkle.core.utils.common

sealed class ResultWrapper<out T> {
    data class Success<out T>(val value: T) : ResultWrapper<T>()
    data class GenericError(
        val code: Int? = null,
        val error: String? = null,
        val type: String? = null
    ) : ResultWrapper<Nothing>()

    object NetworkError : ResultWrapper<Nothing>()
}