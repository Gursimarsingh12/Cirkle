package com.app.cirkle.core.components

import android.content.Context
import android.util.AttributeSet
import androidx.appcompat.widget.AppCompatImageView
import androidx.core.content.ContextCompat
import com.app.cirkle.R

class CheckMark @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : AppCompatImageView(context, attrs, defStyleAttr) {

    private var type: Int = 2 // default to "nothing"

    init {
        attrs?.let {
            val typedArray = context.theme.obtainStyledAttributes(attrs,R.styleable.AccountIdentity,0,0)
                .apply {
                try {
                    val state = getInt(R.styleable.AccountIdentity_accountType, 0)
                    type=state
                } finally {
                    recycle()
                }
            }
        }
        updateDrawable()
    }

    fun setAccountType(newType: Int) {
        type = newType
        updateDrawable()
    }

    private val primeDrawable =ContextCompat.getDrawable(context, R.drawable.prime_drawable)
    private val privateDrawable =ContextCompat.getDrawable(context, R.drawable.public_drawable)
    private var combinedDrawable= ContextCompat.getDrawable(context, R.drawable.prime_public_drawable)

    private fun updateDrawable() {
        when (type) {
            0 -> {
                setImageDrawable(primeDrawable)
                visibility = VISIBLE
            }
            1 -> {
                setImageDrawable(privateDrawable)
                visibility = VISIBLE
            }
            2 -> {
                setImageDrawable(null)
                visibility = GONE
            }
            3 -> {
                setImageDrawable(combinedDrawable)
                visibility = VISIBLE
            }
        }
    }

}