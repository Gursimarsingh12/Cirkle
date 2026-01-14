package com.app.cirkle.data.model.user.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class MutualFollower(
    @Json(name = "user_id") val userId: String,
    @Json(name = "name") val name: String
)

@JsonClass(generateAdapter = true)
data class UserProfileResponse(
    @Json(name = "user_id") val id: String,
    @Json(name="name")val name: String,
    @Json(name = "followers_count") val followerCount: Int,
    @Json(name = "following_count") val followingCount: Int,
    @Json(name = "photo") val profileUrl: String?,
    @Json(name = "banner") val bannerUrl: String? = "",
    @Json(name="is_private") val isPrivate:Boolean,
    @Json(name="is_organizational") val isOrganizational: Boolean,
    @Json(name="is_prime") val isPrime: Boolean,
    @Json(name="is_online") val isOnline:Boolean,
    @Json(name="bio") val bio: String?,
    @Json(name = "interests") val interests: List<String> = emptyList(),
    @Json(name="command") val command:String? = null,
    @Json(name="mutual_followers") val mutualFollowers:List<MutualFollower> = emptyList(),
    @Json(name = "can_view_content") val canViewContent: Boolean,
    @Json(name="created_at") val createdAt:String,
    @Json(name="updated_at") val updatedAt: String,
    @Json(name = "message") val message:String,
    @Json(name = "follow_status") val followStatus: String?
)


