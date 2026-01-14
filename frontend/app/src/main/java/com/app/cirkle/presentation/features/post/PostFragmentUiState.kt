package com.app.cirkle.presentation.features.post

import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.domain.model.tweet.TweetComplete
import com.app.cirkle.presentation.common.Resource

sealed class PostFragmentUiState {
    object Idle: PostFragmentUiState()
    object Loading : PostFragmentUiState()
    data class Success(val data: TweetComplete) : PostFragmentUiState()
    data class Error(val message: String) : PostFragmentUiState()
    data class CommentPosted(val comment: Comment): PostFragmentUiState()
    data class PostCommentError(val message: String): PostFragmentUiState()
}