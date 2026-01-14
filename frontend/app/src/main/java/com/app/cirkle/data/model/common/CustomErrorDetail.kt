package com.app.cirkle.data.model.common

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class CustomErrorDetail(
    val type: String?,
    @Json(name="message") val message: String?,
)