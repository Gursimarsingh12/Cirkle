package com.app.cirkle.presentation.features.onboarding.follow

data class FollowUser(
    val id: String,
    val name:String,
    val followerCount:String,
    val profileUrl:String,
    val checkMarkState:Int,
    var isFollowing:Boolean=false
)