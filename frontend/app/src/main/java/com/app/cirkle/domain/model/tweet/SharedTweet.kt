package com.app.cirkle.domain.model.tweet

import com.app.cirkle.domain.model.tweet.Tweet

data class SharedTweet(
    val id: Long,
    val tweetId: Long,
    val senderId: String,
    val recipientId: String,
    val message: String?,
    val createdAt: String?,
    val sharedAt: String,
    val senderName: String,
    val recipientName: String,
    val senderProfileUrl: String?,
    val recipientProfileUrl: String?,
    val tweet: Tweet,
    val imageCount: Int,
    val formattedTime: String = ""
) 