package com.app.cirkle.presentation.features.post.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.local.SecuredSharedPreferences
import com.app.cirkle.data.model.tweets.request.PostCommentRequest
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.presentation.features.post.PostFragmentUiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class PostViewModel @Inject constructor(private val repository: TweetRepository,private val prefs: SecuredSharedPreferences): ViewModel() {

    private val _postUiState= MutableStateFlow<PostFragmentUiState>(PostFragmentUiState.Loading)
    val postUiState: StateFlow<PostFragmentUiState> =_postUiState

    private val _tweetId = MutableStateFlow<Long?>(null)

    @OptIn(ExperimentalCoroutinesApi::class)
    val pagedComments: Flow<PagingData<Comment>> = _tweetId
        .filterNotNull()
        .flatMapLatest { id ->
            repository.getPostCommentPaged(id)
        }
        .cachedIn(viewModelScope)

    fun setTweetId(id: Long) {
        _tweetId.value = id
    }
    fun getTweet(id:Long){
        viewModelScope.launch {
            repository.getTweetById(id).collect {
                when(it){
                    is ResultWrapper.GenericError -> {
                        _postUiState.value= PostFragmentUiState.Error(it.error?:"Unknown Server Error")
                    }
                    ResultWrapper.NetworkError -> {
                        _postUiState.value= PostFragmentUiState.Error("Server unreachable")
                    }
                    is ResultWrapper.Success ->{
                       _postUiState.value= PostFragmentUiState.Success(it.value)
                    }
                }
            }
        }

    }

    fun postComment(text:String,tweetId:Long){
        viewModelScope.launch {
            _postUiState.value= PostFragmentUiState.Loading
            repository.postComment(PostCommentRequest(tweetId,text)).collect {
                when(it){
                    is ResultWrapper.GenericError -> {
                        _postUiState.value= PostFragmentUiState.PostCommentError(it.error?:"Unknown error")
                    }
                    ResultWrapper.NetworkError -> {
                        _postUiState.value= PostFragmentUiState.PostCommentError("Server unreachable")
                    }
                    is ResultWrapper.Success-> {
                        _postUiState.value= PostFragmentUiState.CommentPosted(it.value)
                    }
                }
            }
        }
    }

    // Pending delete and report
    fun setStateIdle(){
        _postUiState.value= PostFragmentUiState.Idle
    }
    fun isUserCreator(postUserId:String): Boolean{
        return prefs.getUserId()==postUserId
    }

    fun getProfileUrl():String{
        val id=prefs.getUserId()
        return "user/$id/photo/${id}_photo.jpeg"
    }


}