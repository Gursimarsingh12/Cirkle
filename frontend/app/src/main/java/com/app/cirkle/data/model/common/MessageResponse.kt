package com.app.cirkle.data.model.common

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class MessageResponse(
    @Json(name="message")val message:String,
    @Json(name = "success") val success: Boolean?,
)