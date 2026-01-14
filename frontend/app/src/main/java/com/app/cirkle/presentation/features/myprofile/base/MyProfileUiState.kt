package com.app.cirkle.presentation.features.myprofile.base

import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.domain.model.user.MyProfile

data class MyProfileUiState(
    val profileState: ProfileState = ProfileState.Loading,
    val isRefreshing: Boolean = false
)

sealed interface ProfileState {
    data object Loading : ProfileState
    data class Success(val myProfile: MyProfile) : ProfileState
    data class Error(val message: String) : ProfileState
}



//sealed class MyProfileUiState{
//    object Loading: MyProfileUiState()
//    object Idle: MyProfileUiState()
//    data class DataLoaded(val userProfile: UserProfile,val tweets:List<Tweet>): MyProfileUiState()
//    data class Error(val message:String): MyProfileUiState()
//}
