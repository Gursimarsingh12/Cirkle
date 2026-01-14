package com.app.cirkle.presentation.features.userprofile

import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.domain.model.user.UserProfile

data class UserCounts(
    val followersCount: Int,
    val followingCount: Int
)

sealed class UserProfileUiState{
    object Loading: UserProfileUiState()
    object Idle: UserProfileUiState()
    data class ProfileDataLoaded(val userProfile: UserProfile): UserProfileUiState()
    data class CountsUpdated(val counts: UserCounts): UserProfileUiState()
    data class Error(val message:String): UserProfileUiState()
    object FollowLoading: UserProfileUiState()
    data class FollowSuccess(val message: String, val newFollowStatus: String): UserProfileUiState()
    data class FollowError(val message: String): UserProfileUiState()
}