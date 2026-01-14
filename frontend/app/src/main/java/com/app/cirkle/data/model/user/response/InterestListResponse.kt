package com.app.cirkle.data.model.user.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class InterestListResponse(
    @Json(name="interests")val interests: List<InterestItem>
){
    @JsonClass(generateAdapter = true)
    data class InterestItem(
        @Json(name="id")val id: Int,
        @Json(name="name")val name: String
    )
}
