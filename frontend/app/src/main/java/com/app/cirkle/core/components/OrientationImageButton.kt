package com.app.cirkle.core.components

import android.content.Context
import android.util.AttributeSet
import android.view.View
import androidx.appcompat.widget.AppCompatImageButton
import androidx.core.content.ContextCompat
import com.app.cirkle.R

class OrientationImageButton @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : AppCompatImageButton(context, attrs, defStyleAttr) {

    private var onStateChange: ((isLandScape:Boolean) -> Unit)? = null

    var isOrientationLandScape: Boolean = false
        set(value) {
            field = value
            updateViewState()
            onStateChange?.invoke(value)
        }

    init {

        isClickable=true

        context.theme.obtainStyledAttributes(
            attrs,
            R.styleable.SavedImageView,
            0, 0
        ).apply {
            try {
                val state = getBoolean(R.styleable.OrientationImageButton_isLandscape, false)
                isOrientationLandScape = state // use isSelectedState here!
            } finally {
                recycle()
            }
        }

        background= ContextCompat.getDrawable(context,R.drawable.orientation_button_drawable)

        val padding = dpToPx(12)
        setPadding(padding, padding, padding, padding)

        updateViewState()


        setOnClickListener {
            isOrientationLandScape=!isOrientationLandScape
            updateViewState()
        }
    }
    fun setOnStateChangeListener(listener: (isLandScape:Boolean) -> Unit) {
        onStateChange = listener
    }

    private fun updateViewState() {
        if (isOrientationLandScape) {
            setImageDrawable(ContextCompat.getDrawable(context, R.drawable.crop_portrait_24px))
        } else {
            setImageDrawable(ContextCompat.getDrawable(context, R.drawable.crop_landscape_24px))
        }
    }

    private fun View.dpToPx(dp: Int): Int {
        return (dp * context.resources.displayMetrics.density).toInt()
    }
}