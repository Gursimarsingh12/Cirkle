package com.app.cirkle.data.model.user.response

data class UserShortInfo(
    val created_at: String,
    val follower_id: String,
    val is_organizational: Boolean,
    val is_prime: Boolean,
    val is_private: Boolean,
    val name: String,
    val photo: String?
)