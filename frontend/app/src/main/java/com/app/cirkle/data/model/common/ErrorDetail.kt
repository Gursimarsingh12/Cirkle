package com.app.cirkle.data.model.common

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass


@JsonClass(generateAdapter = true)
data class ErrorDetail(
    val message: String?,
    val details: Map<String, Any>?,
    val type: String?
)