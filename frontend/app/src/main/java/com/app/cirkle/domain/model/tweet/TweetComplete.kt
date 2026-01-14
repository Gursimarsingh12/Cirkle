package com.app.cirkle.domain.model.tweet

class TweetComplete(
    val id: Long,
    val userId: String,
    val userName: String,
    val userProfileUrl: String,
    val isUserOrganization: Boolean = false,
    val isUserPrime: Boolean = false,
    val text: String,
    val mediaCount: Int = 0,
    val media: List<Media> = emptyList(), // Corrected from Unit to Media
    val timeUntilPost: String,
    var likesCount: Int = 0,
    val commentCount: Int = 0,
    var isLiked: Boolean = false,
    var isBookMarked: Boolean = false,
    var comments: MutableList<Comment> =mutableListOf<Comment>()
)