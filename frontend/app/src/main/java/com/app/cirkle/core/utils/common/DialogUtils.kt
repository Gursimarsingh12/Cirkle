package com.app.cirkle.core.utils.common

import android.app.Dialog
import android.content.res.Resources
import android.view.ViewGroup

object DialogUtils {
    fun setCompactWidth(dialog: Dialog?, resources: Resources, marginInDp: Int = 48) {
        val marginInPx = (marginInDp * resources.displayMetrics.density).toInt()
        val params = dialog?.window?.attributes
        params?.width = ViewGroup.LayoutParams.MATCH_PARENT
        params?.horizontalMargin = marginInPx.toFloat() / resources.displayMetrics.widthPixels
        dialog?.window?.attributes = params
        dialog?.window?.setBackgroundDrawableResource(android.R.color.transparent)
    }
} 