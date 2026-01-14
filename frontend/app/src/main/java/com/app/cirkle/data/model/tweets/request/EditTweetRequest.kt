package com.app.cirkle.data.model.tweets.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
 
@JsonClass(generateAdapter = true)
data class EditTweetRequest(
    @Json(name = "text") val text: String
) 