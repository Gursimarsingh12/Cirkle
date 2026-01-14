package com.app.cirkle.domain.model.tweet

data class MyComment(
    val id: Int,
    val tweetId: Int,
    val userId: String,
    val text: String,
    val likesCount:String,
    val isLiked:Boolean,
    val parentCommentId: Int, // nullable
    val timeCreatedBefore:String,
    val postCreatorName: String,
)