package com.app.cirkle.domain.model.tweet

data class Tweet(
    var id: Long,
    val userId: String,
    val userName: String,
    val userProfileUrl: String,
    val isUserOrganization: Boolean = false,
    val isUserPrime: Boolean = false,
    var text: String,
    var mediaCount: Int = 0,
    var media: List<Media> = emptyList(), // Corrected from Unit to Media
    val timeUntilPost: String,
    var likesCount: Int = 0,
    val commentCount: Int = 0,
    var isLiked: Boolean = false,
    var isBookMarked: Boolean = false,
    var editedAt: String? = null,
    var isEdited: Boolean = false
)