package com.app.cirkle.presentation.features.post.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.presentation.features.post.EditTweetImage
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class EditTweetViewModel @Inject constructor(
    private val tweetRepository: TweetRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<EditTweetUiState>(EditTweetUiState.Idle)
    val uiState: StateFlow<EditTweetUiState> = _uiState.asStateFlow()

    fun editTweet(tweetId: Long, text: String, keptExistingUrls: List<String>, newFiles: List<java.io.File>) {
        viewModelScope.launch {
            _uiState.value = EditTweetUiState.Loading
            tweetRepository.editTweet(tweetId, text, keptExistingUrls, newFiles).collect { result ->
                when (result) {
                    is ResultWrapper.Success -> _uiState.value = EditTweetUiState.Success(result.value)
                    is ResultWrapper.GenericError -> _uiState.value = EditTweetUiState.Error(result.error ?: "Unknown error")
                    ResultWrapper.NetworkError -> _uiState.value = EditTweetUiState.Error("Network error. Please try again.")
                }
            }
        }
    }
}

sealed class EditTweetUiState {
    object Idle : EditTweetUiState()
    object Loading : EditTweetUiState()
    data class Success(val tweet: Tweet) : EditTweetUiState()
    data class Error(val message: String) : EditTweetUiState()
} 