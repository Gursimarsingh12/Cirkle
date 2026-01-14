package com.app.cirkle.data.model.common

import com.squareup.moshi.Moshi
import com.squareup.moshi.JsonClass
import retrofit2.HttpException
@JsonClass(generateAdapter = true)
data class ErrorResponse(
    val detail: List<ErrorDetail>?,
)









