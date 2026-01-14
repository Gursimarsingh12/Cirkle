package com.app.cirkle.data.model.auth.request


import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class RegisterRequest(
    @Json(name = "user_id") val userId: String,
    @Json(name="password") val password: String,
    @Json(name="name") val name: String,
    @Json(name = "date_of_birth") val dateOfBirth: String,
    @Json(name = "command_id") val commandId: Int
)