package com.app.cirkle.presentation.features.activity.common

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.activity.addCallback
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.google.android.material.tabs.TabLayoutMediator
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentActivityBinding
import com.app.cirkle.presentation.adapters.ActivityViewPagerAdapter
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class ActivityFragment : Fragment() {

    private var _binding:FragmentActivityBinding?=null
    private val binding
        get()=_binding!!

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        requireActivity().onBackPressedDispatcher.addCallback(this) {
            findNavController().navigate(R.id.action_return_to_home)
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View{
        _binding= FragmentActivityBinding.inflate(inflater)
        // Inflate the layout for this fragment
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val adapter = ActivityViewPagerAdapter(requireActivity())
        binding.viewpager.adapter = adapter

        TabLayoutMediator(binding.tabLayout, binding.viewpager) { tab, position ->
            tab.text = when (position) {
                0 -> "Likes"
                1 -> "Comments"
                2 -> "Saved"
                else -> ""
            }
        }.attach()
    }

    override fun onDestroy() {
        super.onDestroy()
        _binding=null
    }


}

