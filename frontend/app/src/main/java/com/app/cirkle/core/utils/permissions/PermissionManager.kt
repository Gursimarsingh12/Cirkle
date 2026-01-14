package com.app.cirkle.core.utils.permissions

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat

object PermissionManager {
    fun hasCameraPermissions(context: Context): Boolean{
        return ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA)== PackageManager.PERMISSION_GRANTED
    }
}