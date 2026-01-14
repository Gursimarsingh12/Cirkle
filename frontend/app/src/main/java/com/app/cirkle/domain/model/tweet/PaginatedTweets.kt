package com.app.cirkle.domain.model.tweet

import com.app.cirkle.domain.model.tweet.Tweet

data class PaginatedTweets (
    val tweets: MutableList<Tweet>,
    val total:Int,
    val page:Int,
    val pageSize:Int,
)