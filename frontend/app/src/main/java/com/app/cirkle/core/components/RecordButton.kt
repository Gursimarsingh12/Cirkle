package com.app.cirkle.core.components

import android.content.Context
import android.graphics.drawable.Animatable
import android.util.AttributeSet
import androidx.appcompat.widget.AppCompatImageView
import androidx.vectordrawable.graphics.drawable.AnimatedVectorDrawableCompat
import com.app.cirkle.R


class RecordButton @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null
) : AppCompatImageView(context, attrs) {

    var onCaptureClick: (() -> Unit)? = null

    private val scaleUp by lazy {
        AnimatedVectorDrawableCompat.create(context, R.drawable.avd_camera_controller_scale_up)
    }

    private val scaleDown by lazy {
        AnimatedVectorDrawableCompat.create(context, R.drawable.avd_camera_controller_scale_down)
    }

    init {
        setImageDrawable(scaleUp)
        scaleType = ScaleType.CENTER_INSIDE
        isClickable = true
        isFocusable = true

        setOnClickListener {
            playScaleAnimation()
            onCaptureClick?.invoke()
        }
    }

    private fun playScaleAnimation() {
        setImageDrawable(scaleUp)
        (drawable as? Animatable)?.start()

        // Chain scaleDown after 300ms (duration of scaleUp)
        postDelayed({
            setImageDrawable(scaleDown)
            (drawable as? Animatable)?.start()
        }, 300)
    }
}