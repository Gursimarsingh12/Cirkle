package com.app.cirkle.data.model.user.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class AddInterestsRequest(
    @Json(name="interest_ids")val interestIds: List<Int>
)