package com.app.cirkle.data.model.common

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class CustomErrorResponse(
    val detail: CustomErrorDetail,
)