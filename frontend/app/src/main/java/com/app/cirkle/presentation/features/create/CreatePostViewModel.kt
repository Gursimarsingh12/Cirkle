package com.app.cirkle.presentation.features.create

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.model.tweets.request.PostTweetRequest
import com.app.cirkle.data.remote.mappers.UserProfileMapper.toDomainModel
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@HiltViewModel
class CreatePostViewModel @Inject constructor(
    private val userRepository: UserRepository,
    private val tweetRepository: TweetRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<CreatePostUiState>(CreatePostUiState.Idle)
    val uiState: StateFlow<CreatePostUiState> = _uiState




    init {
        fetchUserProfile()
    }

    private fun fetchUserProfile() {
        _uiState.value = CreatePostUiState.Loading

        viewModelScope.launch {
            userRepository.getMyProfile().collect { result ->
                _uiState.value = when (result) {
                    is ResultWrapper.Success -> {
                        val userProfile = result.value.toDomainModel()
                        CreatePostUiState.Success(userProfile)
                    }

                    is ResultWrapper.GenericError -> {
                        CreatePostUiState.Error(result.error ?: "Unknown server error.")
                    }

                    ResultWrapper.NetworkError -> {
                        CreatePostUiState.Error("Please check your network connection.")
                    }
                }
            }
        }
    }

    fun postTweet(text: String,files: MutableList<File>) {
        _uiState.value = CreatePostUiState.Loading

        viewModelScope.launch {

            tweetRepository.postTweet(text,files).collect { result ->
                _uiState.value = when (result) {
                    is ResultWrapper.Success -> {
                        CreatePostUiState.PostSuccess("Tweet posted successfully!")
                    }

                    is ResultWrapper.GenericError -> {
                        Log.d("BackEndError","Wrapped result is: $result")
                        CreatePostUiState.Error(result.error ?: "Failed to post tweet.")
                    }

                    ResultWrapper.NetworkError -> {
                        CreatePostUiState.Error("Please check your network connection.")
                    }
                }
            }
        }
    }
}