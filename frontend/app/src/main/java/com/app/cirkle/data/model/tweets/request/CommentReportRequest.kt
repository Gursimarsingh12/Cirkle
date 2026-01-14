package com.app.cirkle.data.model.tweets.request

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class CommentReportRequest(
    @Json(name="comment_id") val commentId:Long,
    @Json(name="reason") val reason:String,
)
