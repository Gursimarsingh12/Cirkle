package com.app.cirkle.data.model.user.response

import com.squareup.moshi.JsonClass

data class FollowersResponse(
    val followers: List<UserShortInfo>,
    val page: Int,
    val page_size: Int,
    val total: Int,
)

@JsonClass(generateAdapter = true)
data class FollowingResponse(
    val following: List<UserShortInfo>,
    val page: Int,
    val page_size: Int,
    val total: Int,
)

@JsonClass(generateAdapter = true)
data class MutualFollowersResponse(
    val followers: List<UserShortInfo>,
    val page: Int,
    val page_size: Int,
    val total: Int,
    val message: String?
)