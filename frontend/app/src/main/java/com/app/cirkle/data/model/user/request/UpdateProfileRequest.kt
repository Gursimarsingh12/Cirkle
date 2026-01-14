package com.app.cirkle.data.model.user.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class UpdateProfileRequest(
    @Json(name = "name")
    val name: String,
    @Json(name = "bio")
    val bio: String?,
    @Json(name = "photo_url")
    val isPrivate: Boolean?,
    @Json(name = "command_id")
    val commandId: Int?,
    @Json(name = "interest_ids")
    val interestIds: List<Int>?
)