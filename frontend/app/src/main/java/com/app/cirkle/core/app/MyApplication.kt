package com.app.cirkle.core.app

import android.app.Application
import androidx.appcompat.app.AppCompatDelegate
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleObserver
import androidx.lifecycle.OnLifecycleEvent
import androidx.lifecycle.ProcessLifecycleOwner
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject
import com.app.cirkle.domain.repository.AuthRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch

@HiltAndroidApp
class MyApplication : Application(), LifecycleObserver {
    @Inject
    lateinit var authRepository: AuthRepository

    private val appScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    override fun onCreate() {
        super.onCreate()
        AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        ProcessLifecycleOwner.get().lifecycle.addObserver(this)
    }



    @OnLifecycleEvent(Lifecycle.Event.ON_START)
    fun onEnterForeground() {
        setOnlineStatus(true)
    }

    @OnLifecycleEvent(Lifecycle.Event.ON_STOP)
    fun onEnterBackground() {
        setOnlineStatus(false)
    }

    private fun setOnlineStatus(isOnline: Boolean) {
        appScope.launch {
            authRepository.setOnlineStatus(isOnline).collect { /* Optionally handle result */ }
        }
    }
}