package com.app.cirkle.data.model.tweets.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import com.app.cirkle.data.model.common.MediaResponse

@JsonClass(generateAdapter = true)
data class PostTweetRequest(
    @Json(name="text")val text: String,
    @Json(name="media")val media: List<MediaResponse> = emptyList() // Default to empty list
)
