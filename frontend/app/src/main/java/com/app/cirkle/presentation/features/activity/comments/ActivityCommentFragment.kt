package com.app.cirkle.presentation.features.activity.comments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.paging.LoadState
import androidx.recyclerview.widget.LinearLayoutManager
import com.app.cirkle.AppNavigationDirections
import com.app.cirkle.databinding.FragmentActivityCommentBinding
import com.app.cirkle.domain.model.tweet.MyComment
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.core.utils.common.NavUtils
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class ActivityCommentFragment : BaseFragment<FragmentActivityCommentBinding>() {

    private val adapter: MyCommentsAdapter by lazy{ MyCommentsAdapter(){tweetId->
        val action= AppNavigationDirections.actionToFragmentUserPost(tweetId)
        NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
    } }
    private val viewModel: ActivityCommentsViewModel by viewModels()
    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentActivityCommentBinding {
        return FragmentActivityCommentBinding.inflate(inflater)
    }


    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setUpRecycleView()
        setUpDataSource()
    }

    private fun setUpRecycleView(){
        binding.recycleView.layoutManager= LinearLayoutManager(requireContext())
        binding.recycleView.adapter=adapter
        binding.root.setOnRefreshListener {
            adapter.refresh()
        }
    }

    private fun setUpDataSource(){
        lifecycleScope.launch {
            lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.pagedMyComments.collect {
                        adapter.submitData(it)
                    }
                }
                launch {
                    adapter.loadStateFlow.collect {
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
                                val isEmpty = adapter.itemCount == 0
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

