package com.app.cirkle.data.model.user.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class TopAccountsResponse(
    @Json(name="accounts")val accounts: List<TopAccount>
)
