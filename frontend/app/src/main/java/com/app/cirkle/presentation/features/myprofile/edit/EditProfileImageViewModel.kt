package com.app.cirkle.presentation.features.myprofile.edit

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.File

class EditProfileImageViewModel: ViewModel() {

    private val _profileImage = MutableStateFlow<File?>(null)
    val profileImage: StateFlow<File?> = _profileImage

    private val _bannerImage= MutableStateFlow<File?>(null)
    val bannerImage: StateFlow<File?> =_bannerImage

    var bio=""
    var updatedName=""

    fun addBannerImage(file: File){
        _bannerImage.value=file
    }
    fun addProfileImage(file: File){
        _profileImage.value= file
    }

    fun clear(){
        _bannerImage.value=null
        _profileImage.value=null
        bio=""
        updatedName=""
    }
}