package com.app.cirkle.data.model.tweets.response

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class CommentPagedResponse(
    @Json(name="comments")val comments: List<CommentResponse>,
    @Json(name="page")val page:Int,
    @Json(name="page_size")val pageSize:Int,
    @Json(name="total")val total:Int,
)