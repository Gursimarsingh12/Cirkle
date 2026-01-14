package com.app.cirkle.presentation.features.onboarding.interests

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.model.user.request.AddInterestsRequest
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class InterestsViewModel @Inject constructor(private val repository: UserRepository): ViewModel() {
    private val _interestUiState= MutableStateFlow<InterestsUiState>(InterestsUiState.Loading)
    val interestsUiState: StateFlow<InterestsUiState> =_interestUiState

    fun getAllInterest(){
        viewModelScope.launch {
            repository.getAllInterests().collect { state->
                when(state){
                    is ResultWrapper.GenericError -> {
                        _interestUiState.value= InterestsUiState.Error(state.error?:"Unknown Error")
                    }
                    ResultWrapper.NetworkError -> {
                        _interestUiState.value= InterestsUiState.Error("Network Error")
                    }
                    is ResultWrapper.Success->{
                        _interestUiState.value= InterestsUiState.Success(state.value)
                    }
                }
            }
        }
    }

    fun addMultipleInterests(lists:List<Int>){
        viewModelScope.launch {
            _interestUiState.value= InterestsUiState.Loading
            repository.addMultipleInterests(AddInterestsRequest(lists)).collect { state->
                when(state){
                    is ResultWrapper.GenericError -> {
                        _interestUiState.value= InterestsUiState.Error(state.error?:"Unknow Error")
                    }
                    ResultWrapper.NetworkError -> {
                        _interestUiState.value= InterestsUiState.Error("Network Error")
                    }
                    is ResultWrapper.Success-> {
                        _interestUiState.value= InterestsUiState.UpdateComplete
                    }
                }

            }
        }
    }
}