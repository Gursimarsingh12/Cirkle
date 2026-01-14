package com.app.cirkle.core.components

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.ScaleGestureDetector
import androidx.appcompat.widget.AppCompatImageView
import androidx.core.graphics.toColorInt
import androidx.core.graphics.drawable.toBitmap
import kotlin.math.min

class CropImageView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : AppCompatImageView(context, attrs, defStyleAttr) {

    enum class CropMode {
        CIRCLE,
        RECTANGLE_PORTRAIT,
        RECTANGLE_LANDSCAPE
    }

    var cropMode = CropMode.RECTANGLE_PORTRAIT
        set(value) {
            field = value
            invalidate()
        }

    private val cropCircleRadius = dpToPx(150f)
    private val rectWidth = dpToPx(270f)
    private val rectHeight = dpToPx(360f)

    private val overlayPaint = Paint().apply {
        color = "#80000000".toColorInt()
        style = Paint.Style.FILL
        isAntiAlias = true
    }

    private val borderPaint = Paint().apply {
        color = Color.WHITE
        style = Paint.Style.STROKE
        strokeWidth = 4f
        isAntiAlias = true
    }

    private val reusablePath = Path()
    private val reusableRectF = RectF()

    private var scaleGestureDetector: ScaleGestureDetector
    private var matrix: Matrix = Matrix()
    private var scaleFactor = 1f

    init {
        scaleType = ScaleType.MATRIX
        scaleGestureDetector = ScaleGestureDetector(context, ScaleListener())
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        centerImage()
    }

    private fun getRectangleSize(): Pair<Float, Float> {
        return when (cropMode) {
            CropMode.RECTANGLE_PORTRAIT -> Pair(dpToPx(300f), dpToPx(400f))
            CropMode.RECTANGLE_LANDSCAPE -> Pair(dpToPx(400f), dpToPx(300f))
            else -> Pair(0f, 0f) // Not used for circle
        }
    }


    private fun centerImage() {
        drawable?.let {
            val imageWidth = it.intrinsicWidth
            val imageHeight = it.intrinsicHeight
            val scale = min(width.toFloat() / imageWidth, height.toFloat() / imageHeight)

            val dx = (width - imageWidth * scale) / 2f
            val dy = (height - imageHeight * scale) / 2f

            matrix.setScale(scale, scale)
            matrix.postTranslate(dx, dy)
            imageMatrix = matrix
        }
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        val centerX = width / 2f
        val centerY = height / 2f

        reusablePath.reset()
        reusablePath.addRect(0f, 0f, width.toFloat(), height.toFloat(), Path.Direction.CW)

        if (cropMode == CropMode.CIRCLE) {
            reusablePath.addCircle(centerX, centerY, cropCircleRadius, Path.Direction.CCW)
        } else {
            val (rectW, rectH) = getRectangleSize()
            reusableRectF.set(
                centerX - rectW / 2,
                centerY - rectH / 2,
                centerX + rectW / 2,
                centerY + rectH / 2
            )
            reusablePath.addRect(reusableRectF, Path.Direction.CCW)
        }

        canvas.drawPath(reusablePath, overlayPaint)

        if (cropMode == CropMode.CIRCLE) {
            canvas.drawCircle(centerX, centerY, cropCircleRadius, borderPaint)
        } else {
            canvas.drawRect(reusableRectF, borderPaint)
        }
    }


    private var lastTouchX = 0f
    private var lastTouchY = 0f
    private var isDragging = false

    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(event: MotionEvent): Boolean {
        scaleGestureDetector.onTouchEvent(event)

        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                lastTouchX = event.x
                lastTouchY = event.y
                isDragging = true
            }
            MotionEvent.ACTION_MOVE -> {
                if (!scaleGestureDetector.isInProgress && isDragging) {
                    val dx = event.x - lastTouchX
                    val dy = event.y - lastTouchY

                    matrix.postTranslate(dx, dy)
                    imageMatrix = matrix

                    lastTouchX = event.x
                    lastTouchY = event.y
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                isDragging = false
            }
        }

        return true
    }

    private inner class ScaleListener : ScaleGestureDetector.SimpleOnScaleGestureListener() {
        override fun onScale(detector: ScaleGestureDetector): Boolean {
            scaleFactor *= detector.scaleFactor
            scaleFactor = scaleFactor.coerceIn(0.1f, 5.0f)
            matrix.setScale(scaleFactor, scaleFactor, detector.focusX, detector.focusY)
            imageMatrix = matrix
            return true
        }
    }

    fun getCroppedBitmap(): Bitmap? {
        val drawable = drawable ?: return null
        val originalBitmap = drawable.toBitmap()

        val invertedMatrix = Matrix()
        imageMatrix.invert(invertedMatrix)

        val cropRect = getCropRect()
        invertedMatrix.mapRect(cropRect)

        val left = cropRect.left.coerceIn(0f, originalBitmap.width.toFloat())
        val top = cropRect.top.coerceIn(0f, originalBitmap.height.toFloat())
        val width = cropRect.width().coerceAtMost(originalBitmap.width - left)
        val height = cropRect.height().coerceAtMost(originalBitmap.height - top)

        return Bitmap.createBitmap(
            originalBitmap,
            left.toInt(),
            top.toInt(),
            width.toInt(),
            height.toInt()
        )
    }

    private fun getCropRect(): RectF {
        val centerX = width / 2f
        val centerY = height / 2f
        return if (cropMode == CropMode.CIRCLE) {
            RectF(
                centerX - cropCircleRadius,
                centerY - cropCircleRadius,
                centerX + cropCircleRadius,
                centerY + cropCircleRadius
            )
        } else {
            val (rectW, rectH) = getRectangleSize()
            RectF(
                centerX - rectW / 2,
                centerY - rectH / 2,
                centerX + rectW / 2,
                centerY + rectH / 2
            )
        }
    }

    private fun dpToPx(dp: Float): Float {
        return dp * resources.displayMetrics.density
    }
}
