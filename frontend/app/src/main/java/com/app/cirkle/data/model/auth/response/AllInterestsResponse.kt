package com.app.cirkle.data.model.auth.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class AllInterestsResponse(
    @Json(name = "interests") val interests: List<InterestResponse>
)