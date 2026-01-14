package com.app.cirkle.data.model.tweets.response



import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass
import com.app.cirkle.data.model.common.MediaResponse
import com.app.cirkle.domain.model.tweet.Media

@JsonClass(generateAdapter = true)
data class TweetResponse(
    @Json(name = "id") val id: Long,
    @Json(name = "user_id") val userId: String,
    @Json(name = "text") val text: String,
    @Json(name = "media") val media: List<MediaResponse>,
    @Json(name = "view_count") val viewCount: Int,
    @Json(name = "like_count") val likeCount: Int,
    @Json(name = "comment_count") val commentCount: Int,
    @Json(name = "share_count") val shareCount: Int,
    @Json(name = "bookmark_count") val bookmarkCount: Int,
    @Json(name = "is_shared") val isShared: Boolean,
    @Json(name = "is_liked") val isLiked: Boolean,
    @Json(name = "is_bookmarked") val isBookmarked: Boolean,
    @Json(name = "created_at") val createdAt: String,
    @Json(name = "edited_at") val editedAt: String?,
    @Json(name = "user_name") val userName: String,
    @Json(name = "photo") val photoUrl: String?,
    @Json(name = "is_organizational") val isOrganizational: Boolean,
    @Json(name = "is_prime") val isPrime: Boolean,
    @Json(name = "comments") val comments: List<CommentResponse>
)



