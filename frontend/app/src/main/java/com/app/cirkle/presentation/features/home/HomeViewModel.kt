package com.app.cirkle.presentation.features.home

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.app.cirkle.data.model.tweets.request.BookmarkTweetRequest
import com.app.cirkle.data.model.tweets.request.LikeTweetRequest
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.presentation.common.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.last
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: TweetRepository,
) : ViewModel(){
    
    private val _homeUiState: MutableStateFlow<Resource<List<Tweet>>> = MutableStateFlow(Resource.Idle)
    val homeUiState: StateFlow<Resource<List<Tweet>>> = _homeUiState



    val pagedRecommendedTweets: Flow<PagingData<Tweet>> = repository.getRecommendedPaged().cachedIn(viewModelScope)


    suspend fun refreshTweets(): Flow<Boolean> {
        return repository.refreshTweets()
    }



}