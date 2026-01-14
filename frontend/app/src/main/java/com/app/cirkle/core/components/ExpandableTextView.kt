package com.app.cirkle.core.components

import android.content.Context
import android.text.TextPaint
import android.util.AttributeSet
import android.util.Log
import android.view.LayoutInflater
import android.widget.FrameLayout
import android.widget.TextView
import androidx.core.view.isVisible
import com.app.cirkle.R

class ExpandableTextView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : FrameLayout(context, attrs) {

    private val textContent: TextView
    private val toggleButton: TextView
    private var isExpanded = false
    private var collapsedMaxLines = 3
    private var originalText: CharSequence = ""

    companion object {
        private const val COLLAPSED_CHAR_LIMIT = 250
    }

    init {
        LayoutInflater.from(context).inflate(R.layout.expandable_text_view, this, true)
        textContent = findViewById(R.id.text_content)
        toggleButton = findViewById(R.id.toggle_button)
        toggleButton.setOnClickListener { toggleExpansion() }
    }

    private fun toggleExpansion() {
        isExpanded = !isExpanded
        if (originalText.length > COLLAPSED_CHAR_LIMIT) {
            textContent.text = if (isExpanded) originalText else originalText.take(COLLAPSED_CHAR_LIMIT).toString() + "..."
        }
        textContent.maxLines = if (isExpanded) Int.MAX_VALUE else collapsedMaxLines
        toggleButton.text = if (isExpanded) "Read less" else "Read more"
    }

    fun setText(text: CharSequence) {
        originalText = text
        isExpanded = false
        textContent.maxLines = collapsedMaxLines
        // Always set collapsed text first
        val collapsedText = if (text.length > COLLAPSED_CHAR_LIMIT) text.take(COLLAPSED_CHAR_LIMIT).toString() + "..." else text
        textContent.text = collapsedText
        textContent.post {
            val needsReadMore = text.length > COLLAPSED_CHAR_LIMIT || textContent.lineCount > collapsedMaxLines
            if (needsReadMore) {
                textContent.text = if (!isExpanded) collapsedText else text
                toggleButton.isVisible = true
            } else {
                textContent.text = text
                toggleButton.isVisible = false
            }
            textContent.maxLines = if (isExpanded) Int.MAX_VALUE else collapsedMaxLines
        }
    }

    fun setCollapsedMaxLines(lines: Int) {
        collapsedMaxLines = lines
        if (!isExpanded) {
            textContent.maxLines = lines
        }
    }
    
    fun TextView.isTextFullyVisible(collapsedMaxLines:Int,callback: (Boolean) -> Unit) {

        this.post {
            val linesNeeded=this.text.length/this.textSize
            val actualLines = 0
            Log.d("TextView",actualLines.toString())
            callback(collapsedMaxLines < linesNeeded)
        }
    }


}
