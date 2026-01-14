package com.app.cirkle.presentation.features.onboarding.follow

import android.annotation.SuppressLint
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.domain.model.user.User
import com.app.cirkle.core.components.ClickableFollowTopVoices
import com.app.cirkle.core.utils.common.ImageUtils

class FollowUserProfileAdapter(
    private val followUser: (userId: String, follow: Boolean) -> Unit,
    private val imageUtils: ImageUtils
) : RecyclerView.Adapter<FollowUserProfileAdapter.UserViewHolder>() {

    val data: MutableList<FollowUser> = mutableListOf()

    override fun onCreateViewHolder(
        parent: ViewGroup,
        viewType: Int
    ): UserViewHolder {
        return UserViewHolder(ClickableFollowTopVoices(parent.context))
    }

    override fun onBindViewHolder(
        holder: UserViewHolder,
        position: Int
    ) {
        holder.bind(data[position])
    }

    override fun getItemCount(): Int {
        return data.size
    }

    @SuppressLint("NotifyDataSetChanged")
    fun updateAdapter(list: List<FollowUser>) {
        data.clear()
        data.addAll(list)
        notifyDataSetChanged()
    }

    inner class UserViewHolder(val view: ClickableFollowTopVoices) : RecyclerView.ViewHolder(view) {
        fun bind(user: FollowUser) {
            view.onStateChangeListener=null
            view.setUser(user, imageUtils)
            view.onStateChangeListener = { isSelected ->
                data[bindingAdapterPosition].isFollowing=isSelected
                followUser(user.id, isSelected)
            }
        }
    }
}