package com.app.cirkle.presentation.features.shares.adapters

import androidx.fragment.app.Fragment
import androidx.viewpager2.adapter.FragmentStateAdapter
import com.app.cirkle.presentation.features.shares.fragments.ReceivedSharesFragment
import com.app.cirkle.presentation.features.shares.fragments.SentSharesFragment

class MessagesPagerAdapter(fragment: Fragment) : FragmentStateAdapter(fragment) {
    override fun getItemCount(): Int = 2

    override fun createFragment(position: Int): Fragment {
        return when (position) {
            0 -> ReceivedSharesFragment()
            1 -> SentSharesFragment()
            else -> throw IllegalArgumentException("Invalid tab position")
        }
    }
}
