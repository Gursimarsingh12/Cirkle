package com.app.cirkle.presentation.features.home

import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.addCallback
import androidx.core.os.bundleOf
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.paging.LoadState
import androidx.paging.PagingData
import androidx.recyclerview.widget.LinearLayoutManager
import com.app.cirkle.AppNavigationDirections
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.databinding.FragmentHomeBinding
import com.app.cirkle.domain.model.tweet.Media
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.common.BaseTweetsFragment
import com.app.cirkle.presentation.common.Resource
import com.app.cirkle.presentation.features.tweets.TweetsAdapter
import com.app.cirkle.presentation.features.tweets.TweetsViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class HomeFragment : BaseTweetsFragment<FragmentHomeBinding>() {

    private val viewModel: HomeViewModel by viewModels()


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requireActivity().onBackPressedDispatcher.addCallback(this) {
            requireActivity().moveTaskToBack(true)
        }
    }

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentHomeBinding {
        return FragmentHomeBinding.inflate(inflater)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setUpRecycleView()
        observeState()
    }

    private fun setUpRecycleView(){
        binding.recycleView.layoutManager= LinearLayoutManager(requireContext())
        binding.recycleView.adapter = tweetsAdapter
        binding.root.setOnRefreshListener {
            lifecycleScope.launch { viewModel.refreshTweets().collectLatest {
                tweetsAdapter.refresh()
            } }
        }
    }


    private fun observeState(){
        lifecycleScope.launch {
            viewLifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED){
                launch {
                    viewModel.refreshTweets().collectLatest {
                        tweetsAdapter.refresh()
                    }
                }
                launch {
                    viewModel.pagedRecommendedTweets.collectLatest {
                        tweetsAdapter.submitData(it)
                    }
                }
                launch {
                    tweetsAdapter.loadStateFlow.collect { loadStates->
                        when (val refreshState = loadStates.refresh) {
                            is LoadState.Loading -> {
                                binding.root.isRefreshing=true
                                showLoading()
                            }

                            is LoadState.NotLoading -> {
                                hideLoading()
                                binding.root.isRefreshing=false
                                val isEmpty = tweetsAdapter.itemCount == 0
                                binding.recycleView.visibility = if (isEmpty) View.GONE else View.VISIBLE
                                binding.noTweets.visibility = if (isEmpty) View.VISIBLE else View.GONE
                            }

                            is LoadState.Error -> {
                                binding.root.isRefreshing=false
                                hideLoading()
                                Log.d("Backend",refreshState.error.message.toString())
                                Toast.makeText(requireContext(),refreshState.error.message, Toast.LENGTH_LONG).show()
                            }
                        }

                    }
                }

            }
        }
    }

}