package com.app.cirkle.data.model.auth.request


import com.squareup.moshi.Json

data class RefreshRequest(
    @Json(name = "refresh_token") val refreshToken: String
)