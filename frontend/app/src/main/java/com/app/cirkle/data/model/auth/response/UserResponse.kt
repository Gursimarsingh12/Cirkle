package com.app.cirkle.data.model.auth.response

import com.squareup.moshi.Json

data class UserResponse(
    @Json(name = "user_id") val userId: String,
    @Json(name = "is_active") val isActive: Boolean,
    @Json(name = "is_private") val isPrivate: Boolean,
    @Json(name = "is_online") val isOnline: Boolean)