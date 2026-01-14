package com.app.cirkle.presentation.features.activity.likes

import android.os.Bundle
import android.util.Log
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
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.databinding.FragmentActivityLikesBinding
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
class ActivityLikesFragment : BaseTweetsFragment<FragmentActivityLikesBinding>() {

    private val viewModel: ActivityLikesViewModel by viewModels()

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentActivityLikesBinding {
        return FragmentActivityLikesBinding.inflate(inflater)
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
                    viewModel.pagedLikedTweets.collectLatest {
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
                                // Check if the list is empty
                                val isEmpty = tweetsAdapter.itemCount == 0
                                binding.recycleView.visibility = if (isEmpty) View.GONE else View.VISIBLE
                                binding.emptyTweetsView.visibility = if (isEmpty) View.VISIBLE else View.GONE
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
