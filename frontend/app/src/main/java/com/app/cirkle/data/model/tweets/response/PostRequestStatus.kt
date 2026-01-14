package com.app.cirkle.data.model.tweets.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class PostRequestStatus(
    @Json(name="success")val success: Boolean,
    @Json(name="message")val message: String
)