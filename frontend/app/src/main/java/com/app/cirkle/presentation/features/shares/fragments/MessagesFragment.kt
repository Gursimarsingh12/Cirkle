package com.app.cirkle.presentation.features.shares.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.viewModels
import androidx.navigation.fragment.findNavController
import com.google.android.material.tabs.TabLayoutMediator
import com.app.cirkle.databinding.FragmentMessagesBinding
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.features.shares.adapters.MessagesPagerAdapter
import com.app.cirkle.presentation.features.shares.viewmodels.MessagesViewModel
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MessagesFragment : BaseFragment<FragmentMessagesBinding>() {

    private val viewModel: MessagesViewModel by viewModels()

    private lateinit var pagerAdapter: MessagesPagerAdapter

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentMessagesBinding {
        return FragmentMessagesBinding.inflate(inflater)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.root.handleVerticalInsets()
        setupPager()
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
    }

    private fun setupPager() {
        pagerAdapter = MessagesPagerAdapter(this)
        binding.viewPager.adapter = pagerAdapter
        TabLayoutMediator(binding.tabLayout, binding.viewPager) { tab, position ->
            tab.text = if (position == 0) "Received" else "Sent"
        }.attach()
    }
}