package com.app.cirkle.presentation.features.onboarding.follow

sealed class FollowFragmentUiState {
    object Loading: FollowFragmentUiState()
    object UpdateSuccess: FollowFragmentUiState()
    data class DataReceived(val data: List<FollowUser>): FollowFragmentUiState()
    data class Error(val messages: String): FollowFragmentUiState()
}