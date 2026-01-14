package com.app.cirkle.data.model.auth.response


import com.squareup.moshi.Json

data class AuthResponse(
    @Json(name = "access_token") val accessToken: String,
    @Json(name = "refresh_token") val refreshToken: String
)