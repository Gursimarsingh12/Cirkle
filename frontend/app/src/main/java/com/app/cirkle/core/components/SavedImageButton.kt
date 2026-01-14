package com.app.cirkle.core.components

import android.content.Context
import android.util.AttributeSet
import android.view.View
import androidx.appcompat.widget.AppCompatImageButton
import androidx.core.content.ContextCompat
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.DebounceHelper


class SavedImageButton @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : AppCompatImageButton(context, attrs, defStyleAttr) {

    private var onStateChange: ((SavedImageButton, Boolean) -> Unit)? = null

    private var lastClickTime = 0L

    var isSavedState: Boolean = false
        set(value) {
            field = value
            updateViewState()
            onStateChange?.invoke(this, value)
        }

    init {

        isClickable=true

        context.theme.obtainStyledAttributes(
            attrs,
            R.styleable.SavedImageView,
            0, 0
        ).apply {
            try {
                val state = getBoolean(R.styleable.SavedImageView_isSaved, false)
                isSavedState = state // use isSelectedState here!
            } finally {
                recycle()
            }
        }

        val padding = dpToPx(8)
        setPadding(padding, padding, padding, padding)

        updateViewState()


        setOnClickListener {
            val now=System.currentTimeMillis()
            if(now-lastClickTime> DebounceHelper.SAVE_DELAY) {
                lastClickTime=now
                isSavedState = !isSavedState
            }
        }
    }



    fun setOnStateChangeListener(listener: ((SavedImageButton, Boolean) -> Unit)?) {
        onStateChange = listener
    }

    private fun updateViewState() {
        if (isSavedState) {
            background = ContextCompat.getDrawable(context, R.drawable.curved_black_rectangle)
            setImageDrawable(ContextCompat.getDrawable(context, R.drawable.bookmark_white_48px))
        } else {
            background = ContextCompat.getDrawable(context, R.drawable.curved_grey_rectangle)
            setImageDrawable(ContextCompat.getDrawable(context, R.drawable.bookmark_48px))
        }
    }

    private fun View.dpToPx(dp: Int): Int {
        return (dp * context.resources.displayMetrics.density).toInt()
    }

}
