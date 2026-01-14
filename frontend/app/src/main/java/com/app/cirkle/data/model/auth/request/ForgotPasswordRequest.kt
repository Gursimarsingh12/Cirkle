package com.app.cirkle.data.model.auth.request


import com.squareup.moshi.Json

data class ForgotPasswordRequest(
    @Json(name = "user_id") val userId: String,
    @Json(name = "date_of_birth") val dateOfBirth: String,
    @Json(name = "new_password") val newPassword: String
)