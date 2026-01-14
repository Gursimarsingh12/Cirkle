package com.app.cirkle.presentation.features.activity.comments

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.domain.model.tweet.MyComment
import com.app.cirkle.domain.repository.TweetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

@HiltViewModel
class ActivityCommentsViewModel @Inject constructor(repository: TweetRepository): ViewModel() {

    val pagedMyComments: Flow<PagingData<Comment>> =repository.getMyCommentsPaged().cachedIn(viewModelScope)
}