package com.app.cirkle.di

import android.util.Log
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import com.app.cirkle.data.remote.api.AuthApiService
import com.app.cirkle.data.remote.interceptor.AuthInterceptor
import com.app.cirkle.data.remote.api.TweetsApiService
import com.app.cirkle.data.remote.api.UserApiService
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.BASE_URL
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
class AppModule {

    @Provides
    @Singleton
    fun providesRetrofitInstance(
        authInterceptor: AuthInterceptor
    ): Retrofit{
        val loggingInterceptor = HttpLoggingInterceptor { message ->
            Log.d("BackEndResponses", message)
        }.apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val moshi = Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .client(
                OkHttpClient.Builder()
                    .addInterceptor(authInterceptor)
                    .addInterceptor(loggingInterceptor)
                    .build()
            ).build()

    }

    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): AuthApiService=
        retrofit.create(AuthApiService::class.java)


    @Provides
    @Singleton
    fun provideTweetApiService(retrofit: Retrofit): TweetsApiService =
        retrofit.create(TweetsApiService::class.java)

    @Provides
    @Singleton
    fun provideUserApiService(retrofit: Retrofit): UserApiService =
        retrofit.create(UserApiService::class.java)


}