package com.app.cirkle.presentation.features.userprofile

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.domain.model.user.UserProfile
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.domain.repository.UserRepository
import com.app.cirkle.presentation.features.userprofile.UserProfileUiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import kotlinx.coroutines.async
import javax.inject.Inject

@HiltViewModel
class UserProfileViewModel @Inject constructor(private val userRepository: UserRepository,private val tweetRepository: TweetRepository): ViewModel()
{
    private val _uiState= MutableStateFlow<UserProfileUiState>(UserProfileUiState.Loading)
    val uiState: StateFlow<UserProfileUiState> =_uiState
    
    var currentUserProfile: UserProfile? = null
        private set
    
    var currentUserCounts: UserCounts? = null
        private set

    private val _pagedUserTweets = MutableStateFlow<PagingData<Tweet>>(PagingData.empty())
    val pagedUserTweets: StateFlow<PagingData<Tweet>> = _pagedUserTweets

    fun loadUserTweets(userId: String) {
        viewModelScope.launch {
            tweetRepository.getUserTweetsPaged(userId)
                .cachedIn(viewModelScope)
                .collectLatest {
                    _pagedUserTweets.value = it
                }
        }
    }

    fun loadUserProfileData(userId:String){
        viewModelScope.launch {
            userRepository.getUserProfile(userId).collect { profileResult ->
                when(profileResult){
                    is ResultWrapper.GenericError -> {
                        _uiState.value= UserProfileUiState.Error(profileResult.error?:"Server error")
                    }
                    ResultWrapper.NetworkError -> {
                        _uiState.value= UserProfileUiState.Error("Network error")
                    }
                    is ResultWrapper.Success-> {
                        var profile = profileResult.value
                        currentUserProfile = profile
                        
                        // The profile response already contains the correct follower and following counts
                        // Extract counts from profile response
                        val counts = UserCounts(
                            followersCount = profile.followerCount.toIntOrNull() ?: 0,
                            followingCount = profile.followingCount.toIntOrNull() ?: 0
                        )
                        currentUserCounts = counts
                        
                        // Now check the actual following status from the following list
                        userRepository.isFollowingUser(userId).collect { followingResult ->
                            when(followingResult) {
                                is ResultWrapper.Success -> {
                                    val isActuallyFollowing = followingResult.value
                                    // Update the profile with the correct following status
                                    val correctedProfile = profile.copy(
                                        isFollowing = isActuallyFollowing,
                                        followStatus = if (isActuallyFollowing) "following" else profile.followStatus
                                    )
                                    currentUserProfile = correctedProfile
                                    _uiState.value = UserProfileUiState.ProfileDataLoaded(correctedProfile)
                                    
                                    // Emit the counts from the profile response
                                    _uiState.value = UserProfileUiState.CountsUpdated(counts)
                                }
                                is ResultWrapper.GenericError -> {
                                    // If we can't check following status, use the original profile
                                    _uiState.value = UserProfileUiState.ProfileDataLoaded(profile)
                                    // Still emit the counts from the profile response
                                    _uiState.value = UserProfileUiState.CountsUpdated(counts)
                                }
                                ResultWrapper.NetworkError -> {
                                    // If we can't check following status, use the original profile
                                    _uiState.value = UserProfileUiState.ProfileDataLoaded(profile)
                                    // Still emit the counts from the profile response
                                    _uiState.value = UserProfileUiState.CountsUpdated(counts)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Note: These count loading methods are no longer needed since we get counts directly from profile response

    fun refreshCounts(userId: String) {
        // Simply reload the profile data as it contains updated counts
        loadUserProfileData(userId)
    }

    fun loadTweets(page:Int){

    }
    
    fun followUser(userId: String) {
        viewModelScope.launch {
            _uiState.value = UserProfileUiState.FollowLoading
            
            userRepository.followUser(userId).collect { result ->
                when (result) {
                    is ResultWrapper.Success -> {
                        val message = result.value.message
                        
                        // Reload the profile to get the updated status
                        loadUserProfileData(userId)
                        
                        // Refresh counts after successful follow
                        refreshCounts(userId)
                        
                        // Show success message
                        _uiState.value = UserProfileUiState.FollowSuccess(message, "loading")
                    }
                    is ResultWrapper.GenericError -> {
                        _uiState.value = UserProfileUiState.FollowError(result.error ?: "Failed to follow user")
                    }
                    ResultWrapper.NetworkError -> {
                        _uiState.value = UserProfileUiState.FollowError("Network error. Please check your connection.")
                    }
                }
            }
        }
    }
    
    fun unfollowUser(userId: String) {
        viewModelScope.launch {
            _uiState.value = UserProfileUiState.FollowLoading
            
            userRepository.unfollowUser(userId).collect { result ->
                when (result) {
                    is ResultWrapper.Success -> {
                        val message = result.value.message
                        
                        // Reload the profile to get the updated status
                        loadUserProfileData(userId)
                        
                        // Refresh counts after successful unfollow
                        refreshCounts(userId)
                        
                        // Show success message
                        _uiState.value = UserProfileUiState.FollowSuccess(message, "loading")
                    }
                    is ResultWrapper.GenericError -> {
                        _uiState.value = UserProfileUiState.FollowError(result.error ?: "Failed to unfollow user")
                    }
                    ResultWrapper.NetworkError -> {
                        _uiState.value = UserProfileUiState.FollowError("Network error. Please check your connection.")
                    }
                }
            }
        }
    }
}