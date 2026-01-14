package com.app.cirkle.presentation.features.activity.saved

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.core.view.isVisible
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.paging.LoadState
import androidx.recyclerview.widget.LinearLayoutManager
import com.app.cirkle.AppNavigationDirections
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentActivitySavedBinding
import com.app.cirkle.presentation.common.BaseTweetsFragment
import com.app.cirkle.presentation.features.tweets.TweetsAdapter
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

@AndroidEntryPoint
class ActivitySavedFragment : BaseTweetsFragment<FragmentActivitySavedBinding>() {

    private val viewModel:ActivitySavedViewModel by viewModels()

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentActivitySavedBinding {
        return FragmentActivitySavedBinding.inflate(inflater)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setUpRecycleView()
        setUpUi()
    }

    private fun setUpRecycleView(){
        binding.recycleView.layoutManager= LinearLayoutManager(requireContext())
        binding.recycleView.adapter=tweetsAdapter
        binding.root.setOnRefreshListener {
            tweetsAdapter.refresh()
        }
    }

    private fun setUpUi(){
        lifecycleScope.launch {
            viewLifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED){
                launch {
                    viewModel.pagedSavedTweets.collectLatest {
                        tweetsAdapter.submitData(it)
                    }
                }
                launch {
                    tweetsAdapter.loadStateFlow.collect {
                        when(val state=it.refresh) {
                            is LoadState.Loading -> {
                                binding.root.isRefreshing=true
                                binding.tweetsProgressBar.isVisible=true
                                binding.recycleView.isVisible=false
                            }
                            is LoadState.NotLoading -> {
                                binding.root.isRefreshing=false
                                binding.tweetsProgressBar.isVisible=false
                                val isEmpty = tweetsAdapter.itemCount == 0
                                binding.recycleView.isVisible=!isEmpty
                                binding.emptyTweetsView.isVisible = isEmpty
                            }
                            is LoadState.Error -> {
                                binding.root.isRefreshing=false
                                binding.tweetsProgressBar.isVisible=false
                                Toast.makeText(requireContext(),state.error.message, Toast.LENGTH_LONG).show()
                            }
                        }
                    }
                }
            }
        }
    }



}