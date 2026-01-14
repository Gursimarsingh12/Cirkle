package com.app.cirkle.data.model.user.response

data class FollowRequestsResponse(
    val follow_requests: List<FollowRequestInfo>,
    val page: Int,
    val page_size: Int,
    val total: Int
)

data class FollowRequestInfo(
    val follower_id: String,
    val name: String,
    val photo_url: String?,
    val created_at: String
) 