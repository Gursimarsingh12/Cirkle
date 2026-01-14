package com.app.cirkle.data.model.tweets.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass


@JsonClass(generateAdapter = true)
data class FeedQueryParams(
    @Json(name = "page")
    val page: Int = 1,

    @Json(name = "page_size")
    val pageSize: Int = 20,

    @Json(name = "include_recommendations")
    val includeRecommendations: Boolean = true,

    @Json(name = "feed_type")
    val feedType: String = FeedType.LATEST.value,  // ✅ Enum value

    @Json(name = "last_tweet_id")
    val lastTweetId: Long? = null,

    @Json(name = "refresh")
    val refresh: Boolean = true
) {
    enum class FeedType(val value: String) {
        LATEST("latest"),
        OLDER("older")
    }
}


