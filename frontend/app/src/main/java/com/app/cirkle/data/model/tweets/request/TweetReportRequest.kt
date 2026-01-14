package com.app.cirkle.data.model.tweets.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass


@JsonClass(generateAdapter = true)
data class TweetReportRequest(
    @Json(name = "tweet_id") val tweetId:Long,
    @Json(name="reason") val reason:String,
)