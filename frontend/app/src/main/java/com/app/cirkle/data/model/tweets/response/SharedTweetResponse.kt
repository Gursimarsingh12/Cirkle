package com.app.cirkle.data.model.tweets.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class SharedTweetResponse(
    @Json(name = "id") val id: Long,
    @Json(name = "tweet_id") val tweetId: Long,
    @Json(name = "sender_id") val senderId: String,
    @Json(name = "sender_name") val senderName: String,
    @Json(name = "sender_photo_path") val senderPhotoPath: String?,
    @Json(name = "recipient_id") val recipientId: String,
    @Json(name = "recipient_name") val recipientName: String,
    @Json(name = "recipient_photo_path") val recipientPhotoPath: String?,
    @Json(name = "message") val message: String?,
    @Json(name = "shared_at") val sharedAt: String,
    @Json(name = "created_at") val createdAt: String? = null,
    @Json(name = "tweet") val tweet: TweetResponse,
    @Json(name = "image_count") val imageCount: Int = 0
)