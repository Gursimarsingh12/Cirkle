package com.app.cirkle.data.model.user.response

data class MyProfileResponse(
    val user_id: String,
    val name: String,
    val bio: String?,
    val photo: String?,
    val banner: String?,
    val is_private: Boolean,
    val is_organizational: Boolean,
    val is_prime: Boolean,
    val is_online: Boolean,
    val followers_count: Int,
    val following_count: Int,
    val interests: List<String>,
    val command: String?,
    val mutual_followers: List<String>,
    val can_view_content: Boolean,
    val created_at: String,
    val updated_at: String,
    val message: String?,
    val follow_status:String,
)