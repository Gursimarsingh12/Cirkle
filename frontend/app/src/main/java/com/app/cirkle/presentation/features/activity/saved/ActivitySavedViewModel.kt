package com.app.cirkle.presentation.features.activity.saved

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
class ActivitySavedViewModel @Inject constructor(val repository: TweetRepository):ViewModel() {
    private val _uiState = MutableStateFlow<Resource<List<Tweet>>>(Resource.Loading)
    val uiState: StateFlow<Resource<List<Tweet>>> = _uiState

    val pagedSavedTweets: Flow<PagingData<Tweet>> = repository.getBookmarkedPaged().cachedIn(viewModelScope)

    fun getLikedTweets() {
        viewModelScope.launch {
            repository.getBookmarkedPaged(1).collect { state ->
                when (state) {
                    is ResultWrapper.GenericError -> {
                        _uiState.value =
                            Resource.Error(state.error ?: "Unknown server error")
                    }

                    ResultWrapper.NetworkError -> {
                        _uiState.value = Resource.Error("Network error")
                    }

                    is ResultWrapper.Success -> {
                        _uiState.value = Resource.Success(state.value.tweets)
                    }
                }
            }
        }
    }
}