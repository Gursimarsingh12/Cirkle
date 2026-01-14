package com.app.cirkle.di


import com.app.cirkle.data.repositoryimpl.AuthRepositoryImpl
import com.app.cirkle.data.repositoryimpl.TweetRepositoryImpl
import com.app.cirkle.data.repositoryimpl.UserRepositoryImpl
import com.app.cirkle.domain.repository.AuthRepository
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.domain.repository.UserRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindsAuthRepository(
        impl: AuthRepositoryImpl
    ): AuthRepository

    @Binds
    @Singleton
    abstract fun bindsTweetRepository(
        impl: TweetRepositoryImpl
    ): TweetRepository

    @Binds
    @Singleton
    abstract fun bindsUserRepository(
        impl: UserRepositoryImpl
    ): UserRepository
}
