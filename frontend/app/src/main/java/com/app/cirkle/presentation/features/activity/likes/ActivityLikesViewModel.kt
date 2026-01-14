package com.app.cirkle.presentation.features.activity.likes

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.presentation.common.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ActivityLikesViewModel @Inject constructor(val repository: TweetRepository): ViewModel() {
    private val _uiState= MutableStateFlow<Resource<List<Tweet>>>(Resource.Loading)
    val uiState: StateFlow<Resource<List<Tweet>>> =_uiState

    val pagedLikedTweets: Flow<PagingData<Tweet>> = repository.getLikedPaged().cachedIn(viewModelScope)

    fun getLikedTweets(){
        viewModelScope.launch {
            repository.getLiked(1).collect {
                    state->
                when(state){
                    is ResultWrapper.GenericError -> {
                        _uiState.value=Resource.Error(state.error?:"Unknown server error")
                    }
                    ResultWrapper.NetworkError -> {
                        _uiState.value= Resource.Error("Network error")
                    }
                    is ResultWrapper.Success -> {
                        _uiState.value= Resource.Success(state.value.tweets)
                    }
                }
            }
        }
    }
}

