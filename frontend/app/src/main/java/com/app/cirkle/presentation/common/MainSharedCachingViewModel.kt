package com.app.cirkle.presentation.common

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.local.SecuredSharedPreferences
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import okhttp3.Dispatcher
import javax.inject.Inject

@HiltViewModel
class MainSharedCachingViewModel @Inject constructor(private val userRepository: UserRepository,private val prefs: SecuredSharedPreferences): ViewModel() {

    private val _hasFollowRequests= MutableStateFlow<Boolean>(false)
    val hasFollowRequestState: StateFlow<Boolean> =_hasFollowRequests.asStateFlow()

    fun hasFollowRequests(){
        viewModelScope.launch(Dispatchers.IO) {
            userRepository.getFollowRequests(1, 1).collectLatest {
                when (it) {
                    is ResultWrapper.GenericError -> {
                        _hasFollowRequests.value = false
                    }

                    ResultWrapper.NetworkError -> {
                        _hasFollowRequests.value = false
                    }

                    is ResultWrapper.Success -> {
                        _hasFollowRequests.value = it.value.total != 0
                    }
                }
            }
        }
    }

    fun logout(){
        prefs.clear()
    }

}