package com.app.cirkle.data.remote.interceptor

import com.app.cirkle.data.local.SecuredSharedPreferences
import com.app.cirkle.data.model.auth.request.RefreshRequest
import com.app.cirkle.data.remote.api.AuthApiService
import javax.inject.Inject

class TokenManager @Inject constructor(
    private val apiService: AuthApiService,
    private val prefs: SecuredSharedPreferences
) {
    suspend fun refreshToken() {
        val refreshToken = prefs.getRefreshToken() ?: throw Exception("No refresh token")
        val response = apiService.refreshToken(RefreshRequest(refreshToken))
        prefs.saveJwtToken(response.accessToken)
    }
}