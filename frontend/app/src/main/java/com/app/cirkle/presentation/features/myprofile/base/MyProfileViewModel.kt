package com.app.cirkle.presentation.features.myprofile.base

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.local.SecuredSharedPreferences
import com.app.cirkle.data.remote.mappers.UserProfileMapper.toDomainModel
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class MyProfileViewModel @Inject constructor(
    private val userRepository: UserRepository,
    private val tweetRepository: TweetRepository,
    private val securedSharedPreferences: SecuredSharedPreferences
) : ViewModel() {

    private val _userProfileState = MutableStateFlow(MyProfileUiState())
    val userProfileState: StateFlow<MyProfileUiState> = _userProfileState.asStateFlow()

    val myTweets:Flow<PagingData<Tweet>> =tweetRepository.getMyTweetsPaged().cachedIn(viewModelScope)

    private var currentPage = 1
    private val pageSize = 20




    fun getMyProfile() {
        viewModelScope.launch {
            _userProfileState.value = _userProfileState.value.copy(
                profileState = ProfileState.Loading
            )

            userRepository.getMyProfile().collectLatest { result ->
                val newProfileState = when (result) {
                    is ResultWrapper.Success -> {
                        result.value.let { userProfileData ->
                            val domainModel = userProfileData.toDomainModel()
                            securedSharedPreferences.saveUserProfileUpdatedAt(domainModel.updatedAt)
                            ProfileState.Success(domainModel)
                        }
                    }
                    is ResultWrapper.GenericError -> {
                        val errorMessage = result.error ?: "An unknown error occurred"
                        ProfileState.Error(errorMessage)
                    }
                    is ResultWrapper.NetworkError -> {
                        ProfileState.Error("Network connection error. Please check your internet connection.")
                    }
                }

                _userProfileState.value = _userProfileState.value.copy(
                    profileState = newProfileState
                )
            }
        }
    }

//    private fun getMyTweets(reset: Boolean = false) {
//        viewModelScope.launch {
//            if (reset) {
//                currentPage = 1
//                _userProfileState.value = _userProfileState.value.copy(
//                    tweetsState = TweetsState.Loading
//                )
//            }

//            tweetRepository.getMyTweets(currentPage, pageSize).collectLatest { result ->
//                val newTweetsState = when (result) {
//                    is ResultWrapper.Success -> {
//                        val paginatedTweets = result.value
//                        val existingTweets = if (reset) {
//                            emptyList()
//                        } else {
//                            (_userProfileState.value.tweetsState as? TweetsState.Success)?.tweets ?: emptyList()
//                        }
//
//                        TweetsState.Success(
//                            tweets = existingTweets + paginatedTweets.tweets,
//                            currentPage = currentPage,
//                            totalPages = (paginatedTweets.total + pageSize - 1) / pageSize,
//                            hasMorePages = currentPage * pageSize < paginatedTweets.total
//                        )
//                    }
//                    is ResultWrapper.GenericError -> {
//                        val errorMessage = result.error ?: "Failed to load tweets"
//                        TweetsState.Error(errorMessage)
//                    }
//                    is ResultWrapper.NetworkError -> {
//                        TweetsState.Error("Network connection error. Please check your internet connection.")
//                    }
//                }
//
//                _userProfileState.value = _userProfileState.value.copy(
//                    tweetsState = newTweetsState
//                )
//            }
//        }
//    }

//    fun loadMoreTweets() {
//        val currentTweetsState = _userProfileState.value.tweetsState
//        if (currentTweetsState is TweetsState.Success && currentTweetsState.hasMorePages) {
//            currentPage++
//            getMyTweets(reset = false)
//        }
//    }
//
//    fun refreshProfile() {
//        _userProfileState.value = _userProfileState.value.copy(isRefreshing = true)
//        loadData()
//        _userProfileState.value = _userProfileState.value.copy(isRefreshing = false)
//    }
}