package com.app.cirkle.presentation.features.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.domain.repository.AuthRepository
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ApplicationSettingsViewModel @Inject constructor(private val repository: AuthRepository): ViewModel() {

    fun logout(){
        viewModelScope.launch {
            repository.logout().collect {
                when(it){
                    is ResultWrapper.GenericError -> {


                    }
                    ResultWrapper.NetworkError -> {


                    }
                    is ResultWrapper.Success-> {


                    }
                }
            }
        }
    }
}