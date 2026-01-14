package com.app.cirkle.core.utils.common

import android.os.Bundle
import androidx.annotation.IdRes
import androidx.navigation.NavController
import androidx.navigation.NavOptions

object NavUtils {
    fun navigateWithSlideAnim(
        navController: NavController,
        @IdRes destinationId: Int,
        args: Bundle? = null
    ) {
        val options = NavOptions.Builder()
            .setEnterAnim(com.app.cirkle.R.anim.slide_in_right)
            .setExitAnim(com.app.cirkle.R.anim.slide_out_left)
            .setPopEnterAnim(com.app.cirkle.R.anim.slide_in_left)
            .setPopExitAnim(com.app.cirkle.R.anim.slide_out_right)
            .build()
        navController.navigate(destinationId, args, options)
    }

    fun navigateWithSlideAnimAndPopUpTo(
        navController: NavController,
        @IdRes destinationId: Int,
        @IdRes popUpToId: Int,
        inclusive: Boolean = false,
        args: Bundle? = null
    ) {
        val options = NavOptions.Builder()
            .setEnterAnim(com.app.cirkle.R.anim.slide_in_right)
            .setExitAnim(com.app.cirkle.R.anim.slide_out_left)
            .setPopEnterAnim(com.app.cirkle.R.anim.slide_in_left)
            .setPopExitAnim(com.app.cirkle.R.anim.slide_out_right)
            .setPopUpTo(popUpToId, inclusive)
            .build()
        navController.navigate(destinationId, args, options)
    }
} 