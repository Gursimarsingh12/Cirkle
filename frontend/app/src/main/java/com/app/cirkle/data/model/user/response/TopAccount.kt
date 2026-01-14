package com.app.cirkle.data.model.user.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class TopAccount(
    @Json(name="user_id")val userId: String,
    @Json(name="name")val name: String,
    @Json(name="photo")val photoUrl: String?,
    @Json(name="followers_count")val followersCount: Int,
    @Json(name="is_organizational")val isOrganizational: Boolean,
    @Json(name="is_prime")val isPrime: Boolean
)