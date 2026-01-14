package com.app.cirkle.data.model.tweets.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass


@JsonClass(generateAdapter = true)
data class CommentResponse(
    @Json(name = "id") val id: Long,
    @Json(name = "tweet_id") val tweetId: Long,
    @Json(name = "user_id") val userId: String,
    @Json(name = "text") val text: String,
    @Json(name = "parent_comment_id") val parentCommentId: Long?,
    @Json(name = "like_count") val likeCount: Int,
    @Json(name = "is_liked") val isLiked: Boolean,
    @Json(name = "created_at") val createdAt: String,
    @Json(name = "edited_at") val editedAt: String?,
    @Json(name = "user_name") val userName: String,
    @Json(name = "photo") val photoUrl: String?,
    @Json(name = "is_organizational") val isOrganizational: Boolean,
    @Json(name = "is_prime") val isPrime: Boolean,
    @Json(name ="tweet_author") val author: Author?,
){
    @JsonClass(generateAdapter = true)
    data class Author(
        @Json(name = "user_id") val userId: String,
        @Json(name="name") val name: String,
        @Json(name="photo") val photo:String?,
        @Json(name="is_organizational")val isOrganizational: Boolean,
        @Json(name="is_prime")val isPrime: Boolean,
    )
}

