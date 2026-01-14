package com.app.cirkle.presentation.features.post.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.domain.repository.TweetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class EditCommentViewModel @Inject constructor(
    private val tweetRepository: TweetRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<EditCommentUiState>(EditCommentUiState.Idle)
    val uiState: StateFlow<EditCommentUiState> = _uiState.asStateFlow()

    fun editComment(commentId: Long, text: String) {
        viewModelScope.launch {
            _uiState.value = EditCommentUiState.Loading
            
            tweetRepository.editComment(commentId, text).collect { result ->
                when (result) {
                    is ResultWrapper.Success -> {
                        _uiState.value = EditCommentUiState.Success(result.value)
                    }
                    is ResultWrapper.GenericError -> {
                        _uiState.value = EditCommentUiState.Error(
                            result.error ?: "Failed to edit comment"
                        )
                    }
                    is ResultWrapper.NetworkError -> {
                        _uiState.value = EditCommentUiState.Error("Network error. Please try again.")
                    }
                }
            }
        }
    }
}

sealed class EditCommentUiState {
    object Idle : EditCommentUiState()
    object Loading : EditCommentUiState()
    data class Success(val comment: Comment) : EditCommentUiState()
    data class Error(val message: String) : EditCommentUiState()
} 