package com.app.cirkle.core.components


import android.content.Context
import android.util.AttributeSet
import android.view.LayoutInflater
import android.widget.FrameLayout
import android.widget.LinearLayout
import androidx.core.content.ContextCompat
import androidx.core.graphics.drawable.toDrawable
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.databinding.FollowTopVoicesItemBinding
import com.app.cirkle.presentation.features.onboarding.follow.FollowUser

class ClickableFollowTopVoices @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : FrameLayout(context, attrs, defStyleAttr) {

    private val binding = FollowTopVoicesItemBinding.inflate(LayoutInflater.from(context), this, true)

    var isSelectedState: Boolean = false
        set(value) {
            field = value
            updateUI()
            onStateChangeListener?.invoke(value)
        }

    var onStateChangeListener: ((Boolean) -> Unit)? = null

    init {
        binding.card.strokeWidth=1.dpToPx()
        updateUI()

        val params = LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        )
        params.setMargins(8.dpToPx(), 8.dpToPx(), 8.dpToPx(), 8.dpToPx())
        layoutParams = params


        binding.card.setOnClickListener {
            isSelectedState = !isSelectedState
        }
    }

    private fun updateUI() {
        if(isSelectedState){
            binding.buttomContainer.setImageDrawable(ContextCompat.getDrawable(context,R.drawable.minus))
            binding.card.background= ContextCompat.getDrawable(context,R.drawable.card_selectable_background)
            binding.card.strokeColor = ContextCompat.getColor(context, R.color.primc_light)
        }else{
            binding.buttomContainer.setImageDrawable(ContextCompat.getDrawable(context,R.drawable.addbtn))
            binding.card.background= ContextCompat.getColor(context,R.color.white).toDrawable()
            binding.card.strokeColor= ContextCompat.getColor(context,R.color.iconbgnotactive)
        }

    }

    fun setUser(user: FollowUser,imageUtils: ImageUtils) {
        isSelectedState=user.isFollowing
        binding.userName.text = user.name
        binding.userId.text="@${user.id}"
        binding.followersCount.text=user.followerCount
        binding.checkMark.setAccountType(user.checkMarkState)
        imageUtils.loadImageIntoImageView(user.profileUrl,binding.profileImage, circleCrop = true)
    }

    // Extension function to convert dp to px
    private fun Int.dpToPx(): Int =
        (this * context.resources.displayMetrics.density).toInt()
}
