package com.app.cirkle.domain.model.notification

data class FollowRequest(
    val id: String,
    val followerId: String,
    val followerName: String,
    val followerProfileUrl: String,
    val timestamp: String,
    val isOrganizational: Boolean = false,
    val isPrime: Boolean = false
) 