package com.app.cirkle.presentation.features.shares.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.cachedIn
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.model.tweets.request.ShareTweetRequest
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.domain.repository.UserRepository
import com.app.cirkle.presentation.common.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ShareViewModel @Inject constructor(
    userRepository: UserRepository,
    private val tweetRepository: TweetRepository
) : ViewModel() {

    private val _shareStatus = MutableStateFlow<Resource<Unit>>(Resource.Idle)
    val shareStatus: StateFlow<Resource<Unit>> = _shareStatus.asStateFlow()

    private val _selectedUsers = MutableStateFlow<Set<String>>(emptySet())
    val selectedUsers: StateFlow<Set<String>> = _selectedUsers.asStateFlow()

    private val _isShareButtonEnabled = MutableStateFlow(false)
    val isShareButtonEnabled: StateFlow<Boolean> = _isShareButtonEnabled.asStateFlow()

    val pagedMutualFollowers = userRepository.getMutualFollowers().cachedIn(viewModelScope)

    fun updateSelectedUsers(users: Set<String>) {
        _selectedUsers.value = users
        _isShareButtonEnabled.value = users.isNotEmpty() && users.size <= 5
    }

    fun shareTweet(tweetId: Long, message: String?) {
        if (_selectedUsers.value.isEmpty()) return
        
        viewModelScope.launch {
            _shareStatus.value = Resource.Loading
            val request = ShareTweetRequest(
                tweetId = tweetId,
                recipientIds = _selectedUsers.value.toList(),
                message = message
            )

            tweetRepository.shareTweet(request).collect { result ->
                _shareStatus.value = when (result) {
                    is ResultWrapper.Success -> Resource.Success(Unit)
                    is ResultWrapper.GenericError -> Resource.Error(result.error ?: "Failed to share tweet.")
                    is ResultWrapper.NetworkError -> Resource.Error("Network error occurred.")
                }
            }
        }
    }
}
