package com.app.cirkle.presentation.features.myprofile.dialog

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.app.cirkle.domain.model.user.MyFollowFollowing
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import com.app.cirkle.data.model.auth.response.BaseMessageResponse
import com.app.cirkle.core.utils.common.ResultWrapper
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

@HiltViewModel
class FollowViewModel @Inject constructor(
    private val repository: UserRepository
) : ViewModel() {
    fun getFollowers(): Flow<PagingData<MyFollowFollowing>> = repository.getFollowers().cachedIn(viewModelScope)
    fun getFollowing(): Flow<PagingData<MyFollowFollowing>> = repository.getFollowing().cachedIn(viewModelScope)

    private val _unfollowState = MutableStateFlow<UnfollowUiState>(UnfollowUiState.Idle)
    val unfollowState: StateFlow<UnfollowUiState> = _unfollowState

    fun unfollowUser(userId: String) {
        viewModelScope.launch {
            _unfollowState.value = UnfollowUiState.Loading
            repository.unfollowUser(userId).collect { result ->
                when (result) {
                    is ResultWrapper.Success -> {
                        _unfollowState.value = UnfollowUiState.Success(result.value.message)
                    }
                    is ResultWrapper.GenericError -> {
                        _unfollowState.value = UnfollowUiState.Error(result.error ?: "Failed to unfollow user")
                    }
                    ResultWrapper.NetworkError -> {
                        _unfollowState.value = UnfollowUiState.Error("Network error. Please check your connection.")
                    }
                }
            }
        }
    }
}

sealed class UnfollowUiState {
    object Idle : UnfollowUiState()
    object Loading : UnfollowUiState()
    data class Success(val message: String) : UnfollowUiState()
    data class Error(val message: String) : UnfollowUiState()
}