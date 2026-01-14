package com.app.cirkle.data.model.tweets.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class PostCommentRequest(
    @Json(name="tweet_id") val tweetId: Long,
    val text: String,
    @Json(name="parent_comment_id") val parentCommentId: Long? = null
)