package com.app.cirkle.presentation.features.notification

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.model.user.request.AcceptFollowRequest
import com.app.cirkle.domain.model.notification.FollowRequest
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class NotificationsViewModel @Inject constructor(
    private val userRepository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<NotificationsUiState>(NotificationsUiState.Loading)
    val uiState: StateFlow<NotificationsUiState> = _uiState

    fun loadFollowRequests() {
        viewModelScope.launch {
            _uiState.value = NotificationsUiState.Loading
            
            userRepository.getFollowRequests(1, 50).collect { result ->
                when (result) {
                    is ResultWrapper.Success -> {
                        Log.d("NotificationsViewModel", "Follow requests received: ${result.value.follow_requests.size}")
                        val followRequests = result.value.follow_requests.map { requestInfo ->
                            Log.d("NotificationsViewModel", "Processing request from: ${requestInfo.name}")
                            FollowRequest(
                                id = requestInfo.follower_id,
                                followerId = requestInfo.follower_id,
                                followerName = requestInfo.name,
                                followerProfileUrl = if (requestInfo.photo_url.isNullOrEmpty()) {
                                    "https://randomuser.me/api/portraits/men/${requestInfo.follower_id.substring(2,4).toInt()}.jpg"
                                } else {
                                    requestInfo.photo_url
                                },
                                timestamp = formatTimestamp(requestInfo.created_at),
                                isOrganizational = false,
                                isPrime = false
                            )
                        }
                        Log.d("NotificationsViewModel", "Emitting success state with ${followRequests.size} requests")
                        _uiState.value = NotificationsUiState.Success(followRequests)
                    }
                    is ResultWrapper.GenericError -> {
                        _uiState.value = NotificationsUiState.Error(result.error ?: "Failed to load follow requests")
                    }
                    ResultWrapper.NetworkError -> {
                        _uiState.value = NotificationsUiState.Error("Network error. Please check your connection.")
                    }
                }
            }
        }
    }

    fun respondToFollowRequest(followerId: String, accept: Boolean) {
        viewModelScope.launch {
            val request = AcceptFollowRequest(accept)
            
            userRepository.respondToFollowRequest(followerId, request).collect { result ->
                when (result) {
                    is ResultWrapper.Success -> {
                        val message = if (accept) {
                            "Follow request accepted"
                        } else {
                            "Follow request declined"
                        }
                        _uiState.value = NotificationsUiState.RequestHandled(message)
                        // Automatically reload the requests after handling
                        loadFollowRequests()
                    }
                    is ResultWrapper.GenericError -> {
                        _uiState.value = NotificationsUiState.Error(result.error ?: "Failed to respond to follow request")
                    }
                    ResultWrapper.NetworkError -> {
                        _uiState.value = NotificationsUiState.Error("Network error. Please check your connection.")
                    }
                }
            }
        }
    }
    
    private fun formatTimestamp(createdAt: String): String {
        return try {
            // For now, just return a simple format
            // You can implement proper time formatting here
            "Just now"
        } catch (e: Exception) {
            "Just now"
        }
    }
} 