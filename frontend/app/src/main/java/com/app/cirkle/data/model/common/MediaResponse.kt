package com.app.cirkle.data.model.common

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class MediaResponse(
    @Json(name ="media_path") val mediaUrl: String,
    @Json(name ="media_type") val mediaType: String
)