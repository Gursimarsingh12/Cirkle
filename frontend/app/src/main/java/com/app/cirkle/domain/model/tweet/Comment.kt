package com.app.cirkle.domain.model.tweet

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

@Parcelize
data class Comment(
    val commentId: Long,
    val tweetId: Long,
    val commentCreatorId: String,
    var text: String,
    val parentCommentId: Long?,
    var commentLikesCount: Int,
    var isLikedByUser: Boolean,
    val createdAt: String,
    val commentCreatorName: String,
    val commentCreatorProfileUrl: String,
    val commentCreatorCheckMarkState: Int,
    val author: Author?=null,
    var editedAt: String? = null,
    var isEdited: Boolean = false
) : Parcelable{
    @Parcelize
    data class Author(
        val userId: String,
        val name: String,
        val photo:String?,
        val checkMarkState:Int,
    ): Parcelable
}
