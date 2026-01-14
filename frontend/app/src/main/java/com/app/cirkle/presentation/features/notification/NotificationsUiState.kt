package com.app.cirkle.presentation.features.notification

import com.app.cirkle.domain.model.notification.FollowRequest

sealed class NotificationsUiState {
    object Loading : NotificationsUiState()
    data class Success(val followRequests: List<FollowRequest>) : NotificationsUiState()
    data class Error(val message: String) : NotificationsUiState()
    data class RequestHandled(val message: String) : NotificationsUiState()
} 