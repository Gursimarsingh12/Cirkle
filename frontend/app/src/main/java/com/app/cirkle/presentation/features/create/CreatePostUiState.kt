package com.app.cirkle.presentation.features.create

import com.app.cirkle.domain.model.user.MyProfile

sealed class CreatePostUiState {
    object Loading : CreatePostUiState()
    data class Success(val myProfile: MyProfile) : CreatePostUiState()
    data class PostSuccess(val message: String) : CreatePostUiState()
    data class Error(val message: String) : CreatePostUiState()
    object Idle : CreatePostUiState()
}