package com.app.cirkle.presentation.features.report

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.presentation.common.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SubmitReportViewModel @Inject constructor(private val repository: TweetRepository): ViewModel() {

    private val _uiState: MutableStateFlow<Resource<Unit>> = MutableStateFlow(Resource.Idle)
    val uiState=_uiState.asStateFlow()

    fun report(id: Long,message: String,isPost: Boolean){
        _uiState.value= Resource.Loading
        if(isPost)
            reportTweet(id,message)
        else
            reportPost(id,message)
    }


    private fun reportTweet(id:Long,message:String){
        viewModelScope.launch {
            repository.reportTweet(id,message).collect {
                when(it){
                    is ResultWrapper.GenericError -> {
                        _uiState.value= Resource.Error(it.error?:"Unknown error")
                    }
                    ResultWrapper.NetworkError ->  {
                        _uiState.value= Resource.Error("Unable to reach the server")
                    }
                    is ResultWrapper.Success ->  {
                        _uiState.value= Resource.Success(Unit)
                    }
                }
            }
        }

    }

    private fun reportPost(id:Long,message: String){
        viewModelScope.launch {
            repository.reportComment(id,message).collect {
                when (it) {
                    is ResultWrapper.GenericError -> {
                        _uiState.value= Resource.Error(it.error?:"Unknown error")
                    }
                    ResultWrapper.NetworkError ->  {
                        _uiState.value= Resource.Error("Unable to reach the server")
                    }
                    is ResultWrapper.Success ->  {
                        _uiState.value= Resource.Success(Unit)
                    }
                }
            }
        }
    }
}