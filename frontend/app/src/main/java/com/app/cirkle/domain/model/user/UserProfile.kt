package com.app.cirkle.domain.model.user

data class UserProfile(
    val id: String,
    val name:String,
    val followerCount:String,
    val followingCount:String,
    val profileUrl:String,
    val checkMarkState:Int,
    val bio:String="",
    val bannerUrl:String="",
    val interests:List<String> =emptyList(),
    val isFollowing:Boolean,
    val followStatus: String = "not_following", // "following", "pending", "not_following"
    val isPrivate: Boolean = false,
    val isOrganizational: Boolean = false,
    val canViewContent: Boolean = false,
    val updatedAt: String = ""
)







