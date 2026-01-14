package com.app.cirkle.core.utils.extensions

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow

object SessionManager {
    private val _logoutFlow = MutableSharedFlow<Unit>()
    val logoutFlow = _logoutFlow.asSharedFlow()

    suspend fun notifyLogout() {
        _logoutFlow.emit(Unit)
    }
}
