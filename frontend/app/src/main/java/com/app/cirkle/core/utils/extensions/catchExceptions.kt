package com.app.cirkle.core.utils.extensions

import android.util.Log
import com.squareup.moshi.Moshi
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.model.common.CustomErrorResponse
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.HttpException
import java.io.IOException


suspend fun <T> catchExceptions(apiCall: suspend () -> T): ResultWrapper<T> {
    return withContext(Dispatchers.IO) {
        try {
            Log.d("Backend","Inside safe call")
            ResultWrapper.Success(apiCall())
        } catch (throwable: Throwable) {
            Log.d("Backend", "Inside safe call catch: ${throwable::class.simpleName} - ${throwable.message}")
            when (throwable) {
                is IOException -> ResultWrapper.NetworkError
                is HttpException -> {
                    Log.d("Backend","Inside safe call catch Http Exception")
                    val code = throwable.code()
                    val errorResponse = parseErrorResponse(throwable)
                    ResultWrapper.GenericError(
                        code,
                        errorResponse?.detail?.message,
                        errorResponse?.detail?.type
                    )
                }
                else -> {
                    Log.d("Backend","Inside safe call else with localized message")
                    ResultWrapper.GenericError(null, throwable.message, null)}
            }
        }
    }
}

suspend fun <T> catchExceptions(
    apiCall: suspend () -> T,
    refreshToken: suspend () -> Unit
): ResultWrapper<T> {
    return withContext(Dispatchers.IO) {
        try {
            Log.d("BackEndError", "Inside safe call")
            ResultWrapper.Success(apiCall())
        } catch (throwable: Throwable) {
            Log.d("BackendBackEndError", "Caught exception: ${throwable::class.simpleName} - ${throwable.message}")
            when (throwable) {
                is IOException -> ResultWrapper.NetworkError

                is HttpException -> {
                    val code = throwable.code()
                    Log.d("BackEndError", "HTTP Exception code: $code")

                    if (code == 401) {
                        // Attempt to refresh the token
                        return@withContext try {
                            refreshToken()
                            // Retry the original API call
                            ResultWrapper.Success(apiCall())
                        } catch (retryThrowable: Throwable) {
                            SessionManager.notifyLogout()
                            Log.d("BackEndError", "Retry failed: ${retryThrowable.message}")
                            val errorResponse = parseErrorResponse(throwable)
                            ResultWrapper.GenericError(
                                code,
                                errorResponse?.detail?.message,
                                errorResponse?.detail?.type
                            )
                        }
                    }

                    val errorResponse = parseErrorResponse(throwable)
                    Log.d("BackEndError","Error response: $errorResponse")
                    ResultWrapper.GenericError(
                        code,
                        errorResponse?.detail?.message,
                        errorResponse?.detail?.type
                    )
                }

                else -> {
                    Log.d("BackEndError", "Unexpected error: ${throwable.localizedMessage}")
                    ResultWrapper.GenericError(null, throwable.message, null)
                }
            }
        }
    }
}


fun parseErrorResponse(throwable: HttpException): CustomErrorResponse? {
    val moshi = Moshi.Builder().build()

    return try {
        val errorBody = throwable.response()?.errorBody()?.string()
        Log.d("BackEndError", "ErrorBody is: $errorBody")

        if (!errorBody.isNullOrEmpty()) {
            val json = errorBody.trim()
            if (json.contains("\"detail\":\"")) {
                val detailValue = Regex("\"detail\"\\s*:\\s*\"([^\"]+)\"")
                    .find(json)
                    ?.groupValues?.getOrNull(1)
                Log.d("BackEndError", "Detected string detail: $detailValue")
                val compatibleJson = """
                    {
                        "detail": {
                            "message": "$detailValue",
                            "type": "unauthenticated"
                        }
                    }
                """.trimIndent()
                val adapter = moshi.adapter(CustomErrorResponse::class.java)
                adapter.fromJson(compatibleJson)
            } else {
                val adapter = moshi.adapter(CustomErrorResponse::class.java)
                adapter.fromJson(json)
            }
        } else {
            null
        }
    } catch (e: Exception) {
        Log.e("BackEndError", "Error parsing response: ${e.message}")
        null
    }
}



