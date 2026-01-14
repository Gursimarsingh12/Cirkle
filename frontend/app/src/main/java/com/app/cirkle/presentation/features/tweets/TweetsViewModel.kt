package com.app.cirkle.presentation.features.tweets

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.local.SecuredSharedPreferences
import com.app.cirkle.data.model.tweets.request.BookmarkTweetRequest
import com.app.cirkle.data.model.tweets.request.LikeTweetRequest
import com.app.cirkle.domain.repository.TweetRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class TweetsViewModel @Inject constructor(
    private val repository: TweetRepository,
    private val securedSharedPreferences: SecuredSharedPreferences
) : ViewModel() {

    fun likeTweet(id:Long,like: Boolean){
        viewModelScope.launch {
            repository.likeTweet(LikeTweetRequest(id,like)).collect {state->
                Log.d("BackEnd",state.toString())
            }
        }
    }

    fun getUserId(): String{
        return securedSharedPreferences.getUserId()
    }

    fun bookMarkTweet(tweetId:Long,save:Boolean){
        viewModelScope.launch {
            repository.bookmarkTweet(BookmarkTweetRequest(tweetId,save)).collect {state->
                Log.d("BackEnd",state.toString())
            }
        }
    }

    fun deleteTweet(tweetId:Long,done:(Boolean)->Unit){
        viewModelScope.launch {
            repository.deleteTweet(tweetId).collect{
                when(it){
                    is ResultWrapper.GenericError -> done(false)
                    ResultWrapper.NetworkError -> done(false)
                    is ResultWrapper.Success -> done(true)
                }
            }
        }
    }
}

