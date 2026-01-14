package com.app.cirkle.core.components

import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.util.AttributeSet
import android.view.ViewGroup
import android.view.ViewGroup.MarginLayoutParams
import androidx.core.content.ContextCompat
import com.google.android.material.textview.MaterialTextView
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.DebounceHelper

class FavoriteTextView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : MaterialTextView(context, attrs, defStyleAttr) {

    private var onStateChange: ((FavoriteTextView, Boolean) -> Unit)? = null

    private var lastClickTime = 0L

    var isSelectedState: Boolean = false
        set(value) {
            field = value
            updateViewState()
            onStateChange?.invoke(this, value)
        }

    init {
        // Load custom attributes if any
        context.theme.obtainStyledAttributes(
            attrs,
            R.styleable.FavoriteTextView,
            0, 0
        ).apply {
            try {
                val state = getBoolean(R.styleable.FavoriteTextView_favoriteState, false)
                isSelectedState = state// use isSelectedState here!
            } finally {
                recycle()
            }
        }
        isClickable=true

        // Apply default styles only if not overridden
        if (text == null) text = "28K"
        if (currentTextColor == Color.TRANSPARENT) {
            setTextColor(ContextCompat.getColor(context, R.color.black))
        }

        if (compoundDrawablePadding == 0) compoundDrawablePadding = dpToPx(4)
        if (paddingStart == 0 && paddingTop == 0 && paddingEnd == 0 && paddingBottom == 0) {
            val padding = dpToPx(8)
            setPadding(padding, padding, padding, padding)
        }

        if (textAlignment == TEXT_ALIGNMENT_INHERIT) {
            textAlignment = TEXT_ALIGNMENT_CENTER
        }

        if (typeface == null || typeface.style != Typeface.BOLD) {
            setTypeface(typeface, Typeface.BOLD)
        }

        if (layoutParams == null) {
            layoutParams = MarginLayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).apply {
                val margin = dpToPx(4)
                setMargins(margin, margin, margin, margin)
            }
        }

        updateViewState()

        setOnClickListener {
            val now=System.currentTimeMillis()
            if(now-lastClickTime> DebounceHelper.LIKE_DELAY) {
                lastClickTime=now
                isSelectedState = !isSelectedState  // use isSelectedState here!
            }
        }
    }

    fun setOnStateChangeListener(listener: ((FavoriteTextView, Boolean) -> Unit)?) {
        onStateChange = listener
    }

    private fun updateViewState() {
        if (isSelectedState) {
            background = ContextCompat.getDrawable(context, R.drawable.bg_chip_selected)
            setCompoundDrawablesWithIntrinsicBounds(
                ContextCompat.getDrawable(context, R.drawable.favorite_red_48px),
                null, null, null
            )
        } else {
            background = ContextCompat.getDrawable(context, R.drawable.curved_grey_rectangle)
            setCompoundDrawablesWithIntrinsicBounds(
                ContextCompat.getDrawable(context, R.drawable.favorite_outline_48px),
                null, null, null
            )
        }
    }

    private fun dpToPx(dp: Int): Int {
        return (dp * context.resources.displayMetrics.density).toInt()
    }
}

