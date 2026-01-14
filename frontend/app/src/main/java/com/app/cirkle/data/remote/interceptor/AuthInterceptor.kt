package com.app.cirkle.data.remote.interceptor

import com.app.cirkle.data.local.SecuredSharedPreferences
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject

class AuthInterceptor @Inject constructor(
    private val securedSharedPreferences: SecuredSharedPreferences
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val requestBuilder =chain.request().newBuilder()
        val token=securedSharedPreferences.getJwtToken()
        if(token.isNullOrEmpty().not()){
            requestBuilder.addHeader("Authorization","Bearer $token")
        }
        return chain.proceed(requestBuilder.build())
    }
}