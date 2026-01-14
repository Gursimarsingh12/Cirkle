package com.app.cirkle.presentation.features.myprofile.edit

import com.app.cirkle.domain.model.user.Interest
import com.app.cirkle.domain.model.user.MyProfile

data class EditProfileUiState(
    val profileState: EditProfileState = EditProfileState.Loading,
    val allInterestsState: AllInterestsState = AllInterestsState.Loading,
    val saveState: SaveState = SaveState.Idle,
    val isLoading: Boolean = false
)

sealed interface EditProfileState {
    data object Loading : EditProfileState
    data class Success(val myProfile: MyProfile) : EditProfileState
    data class Error(val message: String) : EditProfileState
}

sealed interface AllInterestsState {
    data object Loading : AllInterestsState
    data class Success(val interests: List<Interest>) : AllInterestsState
    data class Error(val message: String) : AllInterestsState
}

sealed interface SaveState {
    data object Idle : SaveState
    data object Saving : SaveState
    data object Success : SaveState
    data class Error(val message: String) : SaveState
}

sealed class EditState{
    object Idle: EditState()
    object Loading: EditState()
    data class DataLoaded(val myProfile: MyProfile, val interests:List<Interest>): EditState()
    object UpdateSuccess: EditState()
    data class Error(val message: String): EditState()
}