package com.app.cirkle.data.model.auth.request


import com.squareup.moshi.Json

data class ChangePasswordRequest(
    @Json(name = "old_password") val oldPassword: String,
    @Json(name = "new_password") val newPassword: String
)