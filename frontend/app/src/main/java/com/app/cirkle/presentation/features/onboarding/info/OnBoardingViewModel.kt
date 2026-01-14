package com.app.cirkle.presentation.features.onboarding.info

import androidx.lifecycle.ViewModel
import com.app.cirkle.data.local.SecuredSharedPreferences
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject

@HiltViewModel
class OnBoardingViewModel @Inject constructor(private val pref: SecuredSharedPreferences) :
    ViewModel() {

    suspend fun isLoggedIn(): Boolean{
        return withContext(Dispatchers.IO) {
            pref.isLoggedIn()
        }
    }
}