package com.app.cirkle.domain.model.user

data class MyFollowFollowing(
    val followerId: String,
    val followerName: String,
    val followerProfileUrl: String,
    val timestamp: String,
    val isOrganizational: Boolean = false,
    val isPrime: Boolean = false
)
