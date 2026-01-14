package com.app.cirkle.data.model.auth.response

import com.google.gson.annotations.JsonAdapter
import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class CommandResponse(
    @Json(name = "id") val id: Int,
    @Json(name ="name")val name: String
)
