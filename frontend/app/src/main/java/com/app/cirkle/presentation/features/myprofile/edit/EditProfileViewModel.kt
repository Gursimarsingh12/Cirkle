package com.app.cirkle.presentation.features.myprofile.edit

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.model.user.request.UpdateProfileRequest
import com.app.cirkle.data.remote.mappers.UserProfileMapper.toDomainModel
import com.app.cirkle.domain.model.user.Interest
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@HiltViewModel
class EditProfileViewModel @Inject constructor(
    private val userRepository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(EditProfileUiState())
    val uiState: StateFlow<EditProfileUiState> = _uiState.asStateFlow()

    // Current editing values
    private var _currentName = MutableStateFlow("")
    val currentName: StateFlow<String> = _currentName.asStateFlow()

    private var _currentBio = MutableStateFlow("")
    val currentBio: StateFlow<String> = _currentBio.asStateFlow()

    private var _selectedInterests = MutableStateFlow<List<Interest>>(emptyList())
    val selectedInterests: StateFlow<List<Interest>> = _selectedInterests.asStateFlow()

    init {
        loadUserProfile()
        loadAllInterests()
    }

    private fun loadUserProfile() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                profileState = EditProfileState.Loading
            )

            userRepository.getMyProfile().collectLatest { result ->
                val newProfileState = when (result) {
                    is ResultWrapper.Success -> {
                        val userProfile = result.value.toDomainModel()
                        // Initialize current values
                        _currentName.value = userProfile.name
                        _currentBio.value = userProfile.bio
                        EditProfileState.Success(userProfile)
                    }
                    is ResultWrapper.GenericError -> {
                        val errorMessage = result.error ?: "Failed to load profile"
                        EditProfileState.Error(errorMessage)
                    }
                    is ResultWrapper.NetworkError -> {
                        EditProfileState.Error("Network connection error. Please check your internet connection.")
                    }
                }

                _uiState.value = _uiState.value.copy(
                    profileState = newProfileState
                )
            }
        }
    }

    private fun loadAllInterests() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                allInterestsState = AllInterestsState.Loading
            )

            userRepository.getAllInterests().collectLatest { result ->
                val newInterestsState = when (result) {
                    is ResultWrapper.Success -> {
                        AllInterestsState.Success(result.value)
                    }
                    is ResultWrapper.GenericError -> {
                        val errorMessage = result.error ?: "Failed to load interests"
                        AllInterestsState.Error(errorMessage)
                    }
                    is ResultWrapper.NetworkError -> {
                        AllInterestsState.Error("Network connection error. Please check your internet connection.")
                    }
                }

                _uiState.value = _uiState.value.copy(
                    allInterestsState = newInterestsState
                )
            }
        }
    }

    fun updateName(name: String) {
        _currentName.value = name
    }

    fun updateBio(bio: String) {
        _currentBio.value = bio
    }

    fun addInterest(interest: Interest) {
        val currentList = _selectedInterests.value.toMutableList()
        if (!currentList.any { it.id == interest.id }) {
            currentList.add(interest)
            _selectedInterests.value = currentList
        }
    }

    fun removeInterest(interest: Interest) {
        val currentList = _selectedInterests.value.toMutableList()
        currentList.removeAll { it.id == interest.id }
        _selectedInterests.value = currentList
    }

    fun setSelectedInterests(interests: List<Interest>) {
        _selectedInterests.value = interests
    }

    fun saveProfile(profileImage:File?,bannerImage:File?) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                saveState = SaveState.Saving,
                isLoading = true
            )

            val interestIds = _selectedInterests.value.map { it.id }

            val updateRequest = UpdateProfileRequest(
                name = _currentName.value.trim(),
                bio = _currentBio.value.trim().ifBlank { null },
                isPrivate = true,
                commandId = null,
                interestIds = interestIds
            )

            // Log the request for debugging
            android.util.Log.d("EditProfile", "Saving profile with: ${updateRequest}")
            android.util.Log.d("EditProfile", "Interest IDs: ${interestIds}")

            userRepository.updateProfile(updateRequest,profileImage,bannerImage).collectLatest { result ->
                val newSaveState = when (result) {
                    is ResultWrapper.Success -> {
                        SaveState.Success
                    }
                    is ResultWrapper.GenericError -> {
                        val errorMessage = result.error ?: "Failed to save profile"
                        android.util.Log.e("EditProfile", "Save error: $errorMessage")
                        SaveState.Error(errorMessage)
                    }
                    is ResultWrapper.NetworkError -> {
                        android.util.Log.e("EditProfile", "Network error")
                        SaveState.Error("Network connection error. Please check your internet connection.")
                    }
                }

                _uiState.value = _uiState.value.copy(
                    saveState = newSaveState,
                    isLoading = false
                )
            }
        }
    }

    fun clearSaveState() {
        _uiState.value = _uiState.value.copy(saveState = SaveState.Idle)
    }
}