package com.app.cirkle.domain.model.user

data class User(
    val id: String,
    val name:String,
    val followerCount:String,
    val profileUrl:String,
    val checkMarkState:Int,
)