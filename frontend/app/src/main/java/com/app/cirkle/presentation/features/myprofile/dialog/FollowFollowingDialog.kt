package com.app.cirkle.presentation.features.myprofile.dialog

import android.app.Dialog
import android.os.Bundle
import android.view.ViewGroup
import android.view.Window
import androidx.fragment.app.DialogFragment
import androidx.fragment.app.Fragment
import androidx.viewpager2.adapter.FragmentStateAdapter
import com.google.android.material.tabs.TabLayoutMediator
import com.app.cirkle.databinding.DialogFollowFollowingBinding
import com.app.cirkle.core.utils.common.DialogUtils
import dagger.hilt.android.AndroidEntryPoint

class FollowFollowingDialog : DialogFragment() {

    companion object {
        private const val ARG_INITIAL_PAGE = "initial_page"
        fun newInstance(initialPage: Int): FollowFollowingDialog {
            val dialog = FollowFollowingDialog()
            val args = Bundle()
            args.putInt(ARG_INITIAL_PAGE, initialPage)
            dialog.arguments = args
            return dialog
        }
    }

    private var _binding: DialogFollowFollowingBinding? = null
    private val binding get() = _binding!!

    override fun onCreateDialog(savedInstanceState: Bundle?): Dialog {
        val dialog = Dialog(requireContext())
        _binding = DialogFollowFollowingBinding.inflate(layoutInflater)
        dialog.setContentView(binding.root)
        dialog.window?.setLayout(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        )
        setupViewPager()
        return dialog
    }

    override fun onStart() {
        super.onStart()
        DialogUtils.setCompactWidth(dialog, resources)
    }

    private fun setupViewPager() {
        val adapter = FollowFollowingPagerAdapter(this)
        binding.viewPager.adapter = adapter

        val initialPage = arguments?.getInt(ARG_INITIAL_PAGE, 0) ?: 0
        binding.viewPager.setCurrentItem(initialPage, false)

        TabLayoutMediator(binding.tabLayout, binding.viewPager) { tab, position ->
            tab.text = if (position == 0) "Following" else "Followers"
        }.attach()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private class FollowFollowingPagerAdapter(fragment: Fragment) : FragmentStateAdapter(fragment) {
        override fun getItemCount(): Int = 2
        override fun createFragment(position: Int): Fragment =
            if (position == 0) FollowingFragment() else FollowersFragment()
    }
}
