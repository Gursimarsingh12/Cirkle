package com.app.cirkle.presentation.features.post.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.local.SecuredSharedPreferences
import com.app.cirkle.data.model.tweets.request.LikeCommentRequest
import com.app.cirkle.data.model.tweets.request.PostCommentRequest
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.presentation.common.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CommentRepliesFragmentViewModel @Inject constructor(
    private val prefs: SecuredSharedPreferences,
    private val repository: TweetRepository
):ViewModel(){

    private val _commentId = MutableStateFlow<Long?>(null)

    @OptIn(ExperimentalCoroutinesApi::class)
    val pagedComments: Flow<PagingData<Comment>> = _commentId
        .filterNotNull()
        .flatMapLatest { id ->
            repository.getCommentRepliesPaged(id)
        }
        .cachedIn(viewModelScope)

    fun setCommentId(id:Long){
        _commentId.value=id
    }

    private val _replyUiState: MutableStateFlow<Resource<Unit>> = MutableStateFlow(Resource.Idle)
    val replyUiState:StateFlow<Resource<Unit>> =_replyUiState.asStateFlow()

    fun isUserCreator(postUserId:String): Boolean{
        return prefs.getUserId()==postUserId
    }

    fun getProfileUrl():String{
        val id=prefs.getUserId()
        return "user/$id/photo/${id}_photo.jpeg"
    }

    fun getUserId(): String{
        return prefs.getUserId()
    }

    fun postReply(text:String,tweetId:Long,parentCommentId:Long){
        viewModelScope.launch {
            _replyUiState.value= Resource.Loading
            repository.postComment(PostCommentRequest(tweetId,text,parentCommentId)).collect {
                when(it){
                    is ResultWrapper.GenericError -> {
                        _replyUiState.value= Resource.Error(it.error?:"Unknown error")
                    }
                    ResultWrapper.NetworkError -> {
                        _replyUiState.value= Resource.Error("Server unreachable")
                    }
                    is ResultWrapper.Success-> {
                        _replyUiState.value= Resource.Success(Unit)
                    }
                }
            }
        }
    }

    fun likeComment(commentId:Long,isLiked: Boolean){
        viewModelScope.launch {
            repository.likeComment(LikeCommentRequest(commentId,isLiked)).collect {

            }
        }
    }

    fun setStateIdle(){
        _replyUiState.value= Resource.Idle
    }
}