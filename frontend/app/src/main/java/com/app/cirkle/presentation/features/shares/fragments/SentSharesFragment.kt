package com.app.cirkle.presentation.features.shares.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.os.bundleOf
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.paging.LoadState
import androidx.recyclerview.widget.LinearLayoutManager
import com.app.cirkle.AppNavigationDirections
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentSharesListBinding
import com.app.cirkle.presentation.common.BaseFragment
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import com.app.cirkle.core.utils.common.ImageUtils
import javax.inject.Inject
import com.app.cirkle.core.utils.common.NavUtils
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.presentation.features.shares.viewmodels.MessagesViewModel
import com.app.cirkle.presentation.features.shares.adapters.PagingSharedTweetsAdapter
import com.app.cirkle.presentation.features.tweets.TweetsViewModel

@AndroidEntryPoint
class SentSharesFragment : BaseFragment<FragmentSharesListBinding>() {
    private val viewModel: MessagesViewModel by viewModels({ requireParentFragment() })
    private lateinit var adapter: PagingSharedTweetsAdapter
    private val tweetsViewModel: TweetsViewModel by viewModels()

    @Inject
    lateinit var imageUtils: ImageUtils

    override fun getViewBinding(inflater: LayoutInflater, container: ViewGroup?): FragmentSharesListBinding {
        return FragmentSharesListBinding.inflate(inflater, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupRecyclerView()
        observeShares()
    }

    private fun setupRecyclerView() {
        adapter = PagingSharedTweetsAdapter(
            imageUtils = imageUtils,
            myId = tweetsViewModel.getUserId(),
            onClick = object : PagingSharedTweetsAdapter.TweetItemClickListener {
                override fun onProfileClick(userId: String) {
                    if (userId != tweetsViewModel.getUserId()) {
                        val action = AppNavigationDirections.actionToFragmentUserProfile(userId)
                        NavUtils.navigateWithSlideAnim(
                            findNavController(),
                            action.actionId,
                            action.arguments
                        )
                    }
                }

                override fun onPostClick(tweetId: Long) {
                    val action = AppNavigationDirections.actionToFragmentUserPost(tweetId)
                    NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
                }

                override fun onLikeClick(tweetId: Long, isLiked: Boolean) {
                    tweetsViewModel.likeTweet(tweetId, isLiked)
                }

                override fun onCommentClick(tweetId: Long) {
                    val action = AppNavigationDirections.actionToFragmentUserPost(tweetId)
                    NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
                }

                override fun onSaveClick(tweetId: Long, isSaved: Boolean) {
                    tweetsViewModel.bookMarkTweet(tweetId, isSaved)
                }

                override fun onImageClick(
                    urls: List<String>,
                    startPosition: Int,
                    profileUrl: String,
                    userName: String,
                    userId: String,
                    likeCount: Int
                ) {
                    val bundle = bundleOf(
                        "image_urls" to ArrayList(urls),
                        "start_position" to startPosition,
                        "user_name" to userName,
                        "user_id" to userId,
                        "user_icon_url" to profileUrl,
                        "like_count" to likeCount
                    )
                    NavUtils.navigateWithSlideAnim(
                        findNavController(),
                        R.id.action_to_dialog_image_preview,
                        bundle
                    )
                }

                override fun onShareClick(tweetId: Long) {
                    val action = AppNavigationDirections.actionToShareBottomSheetFragment(tweetId)
                    NavUtils.navigateWithSlideAnim(
                        findNavController(),
                        action.actionId,
                        action.arguments
                    )
                }

                override fun onReportClick(tweetId: Long) {
                    val action = AppNavigationDirections.actionToDialogSubmitAReport(
                        isPost = true,
                        targetId = tweetId
                    )
                    NavUtils.navigateWithSlideAnim(
                        findNavController(),
                        action.actionId,
                        action.arguments
                    )
                }

                override fun onEditClick(tweet: Tweet) {
                    // Not supported in sent list for now
                }

                override fun onDeleteClick(tweetId: Long) {
                    // Not supported in sent list for now
                }
            }
        )
        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        binding.recyclerView.adapter = adapter
    }

    private fun observeShares() {
        lifecycleScope.launch {
            viewLifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.pagedSentShares.collectLatest { pagingData ->
                    adapter.submitData(pagingData)
                }
            }
        }
        adapter.addLoadStateListener { loadStates ->
            binding.progressBar.visibility = if (loadStates.refresh is LoadState.Loading) View.VISIBLE else View.GONE
            val isEmpty = loadStates.refresh is LoadState.NotLoading && adapter.itemCount == 0
            binding.emptyView.visibility = if (isEmpty) View.VISIBLE else View.GONE
        }
    }
}
