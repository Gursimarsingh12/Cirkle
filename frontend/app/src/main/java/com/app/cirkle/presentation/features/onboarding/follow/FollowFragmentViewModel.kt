package com.app.cirkle.presentation.features.onboarding.follow

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class FollowFragmentViewModel @Inject constructor(val repository: UserRepository): ViewModel() {
    private val _uiState = MutableStateFlow<FollowFragmentUiState>(FollowFragmentUiState.Loading)
    val uiState: StateFlow<FollowFragmentUiState> = _uiState

    val accountsFollowed = mutableSetOf<String>()

    fun getTopAccounts() {
        viewModelScope.launch {
            repository.getTopAccounts().collect { result ->
                when(result) {
                    is ResultWrapper.GenericError -> {
                        _uiState.value = FollowFragmentUiState.Error(result.error ?: "Unknown server error")
                    }
                    ResultWrapper.NetworkError -> {
                        _uiState.value = FollowFragmentUiState.Error("Unknown network error")
                    }
                    is ResultWrapper.Success -> {
                        _uiState.value = FollowFragmentUiState.DataReceived(result.value)
                    }
                }
            }
        }
    }

    fun sendFollowRequest(id: String, follow: Boolean) {
        if(follow)
            followAccount(id)
        else
            unfollowAccount(id)
    }

    private fun followAccount(id: String) {
        accountsFollowed.add(id)
        viewModelScope.launch {
            repository.followUser(id).collect {
                // Handle response if needed
            }
        }
    }

    private fun unfollowAccount(id: String) {
        accountsFollowed.remove(id)
        viewModelScope.launch {
            repository.unfollowUser(id).collect {
                // Handle response if needed
            }
        }
    }
}