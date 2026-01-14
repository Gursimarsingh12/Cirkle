package com.app.cirkle.domain.model.tweet

data class ShareChatUser(
    val userId: String,
    val username: String,
    val profileUrl: String?,
    val lastMessage: String?,
    val lastSharedAt: String,
    val unreadCount: Int,
    val formattedTime: String
)

// ShareConversation.kt
data class ShareConversation(
    val message: String?,
    val tweetId: Long,
    val senderId: String,
    val senderName: String,
    val senderProfileUrl: String?,
    val sharedAt: String,
    val tweetText: String?,
    val isSentByMe: Boolean,
    val formattedTime: String
)