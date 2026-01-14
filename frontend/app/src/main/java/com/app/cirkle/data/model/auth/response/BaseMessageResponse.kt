package com.app.cirkle.data.model.auth.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class BaseMessageResponse(
    @Json(name="message")val message: String)