package com.app.cirkle.domain.model.user

data class MyProfile(
    val id: String,
    val name:String,
    val followerCount:String,
    val followingCount:String,
    val profileUrl:String,
    val checkMarkState:Int,
    val bio:String="",
    val bannerUrl:String="",
    val interests:List<String> =emptyList(),
    val updatedAt:String="",
)