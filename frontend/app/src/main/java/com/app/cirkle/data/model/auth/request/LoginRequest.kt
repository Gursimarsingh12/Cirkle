package com.app.cirkle.data.model.auth.request


import com.squareup.moshi.Json

data class LoginRequest(
    @Json(name = "user_id") val userId: String,
    @Json(name="password")val password: String
)
