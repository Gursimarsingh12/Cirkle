package com.app.cirkle.core.components

import android.content.Context
import android.graphics.Color
import android.util.AttributeSet
import android.view.LayoutInflater
import android.view.View
import android.widget.FrameLayout
import androidx.core.content.ContextCompat
import com.app.cirkle.R
import com.app.cirkle.databinding.ViewSelectableChipBinding

class SelectableChipView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : FrameLayout(context, attrs, defStyleAttr) {

    private val binding = ViewSelectableChipBinding.inflate(
        LayoutInflater.from(context), this, true
    )

    private var selectedStateChangeListener:((state:Boolean)->Unit)? =null

    private var isSelectedState = false
    private var textColor: Int = Color.BLACK
    private var textColorSelected: Int = Color.WHITE

    init {
        val a = context.obtainStyledAttributes(attrs, R.styleable.SelectableChipView)
        val chipText = a.getString(R.styleable.SelectableChipView_chipText)
        textColor = a.getColor(R.styleable.SelectableChipView_chipTextColor, Color.BLACK)
        textColorSelected = a.getColor(R.styleable.SelectableChipView_chipTextColorSelected, Color.WHITE)
        isSelectedState = a.getBoolean(R.styleable.SelectableChipView_isChipSelected, false)
        a.recycle()

        chipText?.let { setText(it) }

        updateState()
        val margin = dpToPx(8)
        post {
            val lp = layoutParams
            if (lp is MarginLayoutParams) {
                lp.setMargins(margin, margin, margin, margin)
                layoutParams = lp
            }
        }
        isClickable = true
        isFocusable = true

        setOnClickListener {
            toggle()
        }
    }

    fun setText(text: String) {
        binding.chipText.text = text
    }

    fun setSelectedState(selected: Boolean) {
        isSelectedState = selected
        updateState()
    }

    fun isSelectedState(): Boolean = isSelectedState

    fun toggle() {
//        updateState()
        selectedStateChangeListener?.invoke(isSelectedState)
    }

    private fun updateState() {
        background = ContextCompat.getDrawable(
            context,
            if (isSelectedState) R.drawable.bg_chip_selected else R.drawable.bg_chip_unselected
        )
        binding.chipText.setTextColor(
            if (isSelectedState) textColorSelected else textColor
        )
    }

    fun setOnSelectedStateChangeListener(listener: (Boolean) -> Unit) {
        selectedStateChangeListener = listener
    }

    private fun View.dpToPx(dp: Int): Int {
        return (dp * context.resources.displayMetrics.density).toInt()
    }
}


