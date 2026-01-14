package com.app.cirkle.presentation.features.post.base

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.local.SecuredSharedPreferences
import com.app.cirkle.data.model.tweets.request.LikeCommentRequest
import com.app.cirkle.domain.repository.TweetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CommentViewModel
@Inject constructor(
    private val prefs: SecuredSharedPreferences,
    private val repository: TweetRepository
): ViewModel() {
    fun likeComment(commentId:Long,isLiked: Boolean){
        viewModelScope.launch {
            repository.likeComment(LikeCommentRequest(commentId,isLiked)).collect {

            }
        }
    }

    fun deleteComment(commentId:Long,done:(Boolean)->Unit){
        viewModelScope.launch {
            repository.deleteComment(commentId).collect {
                when(it){
                    is ResultWrapper.GenericError -> {
                        done(false)
                    }
                    ResultWrapper.NetworkError -> {
                        done(false)
                    }
                    is ResultWrapper.Success-> {
                        done(true)
                    }
                }
            }
        }
    }
    fun getUserId():String{
        return prefs.getUserId()
    }
}