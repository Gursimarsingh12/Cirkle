package com.app.cirkle.data.model.auth.request


import com.squareup.moshi.Json

data class OnlineStatusRequest(
    @Json(name = "is_online") val isOnline: Boolean
)