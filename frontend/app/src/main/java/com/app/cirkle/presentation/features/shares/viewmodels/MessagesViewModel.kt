package com.app.cirkle.presentation.features.shares.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.app.cirkle.domain.model.tweet.SharedTweet
import com.app.cirkle.domain.repository.TweetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

@HiltViewModel
class MessagesViewModel @Inject constructor(
    tweetRepository: TweetRepository
) : ViewModel() {

    val pagedReceivedShares: Flow<PagingData<SharedTweet>> =
        tweetRepository.getReceivedSharesPaged().cachedIn(viewModelScope)

    val pagedSentShares: Flow<PagingData<SharedTweet>> =
        tweetRepository.getSentSharesPaged().cachedIn(viewModelScope)
} 