package com.app.cirkle.presentation.adapters

import androidx.fragment.app.Fragment
import androidx.fragment.app.FragmentActivity
import androidx.viewpager2.adapter.FragmentStateAdapter
import com.app.cirkle.presentation.features.activity.comments.ActivityCommentFragment
import com.app.cirkle.presentation.features.activity.likes.ActivityLikesFragment
import com.app.cirkle.presentation.features.activity.saved.ActivitySavedFragment


class ActivityViewPagerAdapter(activity: FragmentActivity) : FragmentStateAdapter(activity) {
    override fun getItemCount(): Int = 3

    override fun createFragment(position: Int): Fragment {
        return when (position) {
            0 -> ActivityLikesFragment()
            1 -> ActivityCommentFragment()
            2-> ActivitySavedFragment()
            else -> throw IllegalArgumentException("Invalid position")
        }
    }
}