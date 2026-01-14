package com.app.cirkle.core.utils.common

import android.view.View
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updatePadding

object WindowInsetsHelper {
    
    /**
     * Applies system window insets to a view that needs bottom padding (e.g. for navigation bar)
     */
    fun View.applyBottomInset() {
        ViewCompat.setOnApplyWindowInsetsListener(this) { view, windowInsets ->
            val insets = windowInsets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.updatePadding(bottom = insets.bottom)
            windowInsets
        }
    }

    /**
     * Applies system window insets to a view that needs both top and bottom padding
     */
    fun View.applyVerticalInsets() {
        ViewCompat.setOnApplyWindowInsetsListener(this) { view, windowInsets ->
            val insets = windowInsets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.updatePadding(
                top = insets.top,
                bottom = insets.bottom
            )
            windowInsets
        }
    }

    /**
     * Applies system window insets to a view that needs all sides padding
     */
    fun View.applyAllInsets() {
        ViewCompat.setOnApplyWindowInsetsListener(this) { view, windowInsets ->
            val insets = windowInsets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.updatePadding(
                left = insets.left,
                top = insets.top,
                right = insets.right,
                bottom = insets.bottom
            )
            windowInsets
        }
    }
} 