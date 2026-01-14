package com.app.cirkle.data.model.tweets.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ShareTweetRequest(
    @Json(name = "message") val message: String?,
    @Json(name = "recipient_ids") val recipientIds: List<String>,
    @Json(name = "tweet_id") val tweetId: Long
)