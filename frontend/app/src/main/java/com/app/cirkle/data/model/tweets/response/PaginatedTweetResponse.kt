package com.app.cirkle.data.model.tweets.response

import com.google.gson.annotations.SerializedName
import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class PaginatedTweetResponse(
    @Json(name = "tweets")val tweets: MutableList<TweetResponse>,
    @Json(name = "total") val total: Int,
    @Json(name="page") val page: Int,
    @Json(name="page_size") val pageSize: Int,
    @Json(name="has_more") val hasMore: Boolean?,
    @Json(name = "feed_type") val feedType: String?,
    @Json(name = "last_tweet_id") val lastTweetId: String?,
    @Json(name = "refresh_timestamp") val timeStamp: String?,
)
