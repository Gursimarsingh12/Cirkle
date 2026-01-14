package com.app.cirkle.data.model.tweets.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class LikeTweetRequest(
    @Json(name="tweet_id")val tweetId: Long,
    @Json(name="like")val like: Boolean
)
