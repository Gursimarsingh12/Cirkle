package com.app.cirkle.presentation.common

import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.fragment.app.viewModels
import androidx.navigation.fragment.findNavController
import androidx.viewbinding.ViewBinding
import com.app.cirkle.AppNavigationDirections
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.core.utils.common.NavUtils
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.presentation.features.post.dialogs.EditTweetDialog
import com.app.cirkle.presentation.features.tweets.TweetsAdapter
import com.app.cirkle.presentation.features.tweets.TweetsViewModel
import javax.inject.Inject

abstract class BaseTweetsFragment<VB : ViewBinding> : BaseFragment<VB>() {

    protected val tweetsViewModel: TweetsViewModel by viewModels()

    @Inject
    lateinit var imageUtils: ImageUtils

    protected val tweetsAdapter: TweetsAdapter by lazy {
        TweetsAdapter(
            tweetsViewModel.getUserId(),
            imageUtils,
            object : TweetsAdapter.OnTweetItemClickListener {
                override fun onProfileClick(userId: String) {
                    val action = AppNavigationDirections.actionToFragmentUserProfile(userId)
                    findNavController().navigate(action)
                }

                override fun onPostClick(tweetId: Long) {
                    val action = AppNavigationDirections.actionToFragmentUserPost(tweetId)
                    NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
                }

                override fun onImageClick(
                    urls: List<String>,
                    currentImage: Int,
                    profileUrl: String,
                    userName: String,
                    userId: String,
                    likeCount: Int
                ) {
                    val bundle = bundleOf(
                        "image_urls" to ArrayList(urls),
                        "start_position" to currentImage,
                        "user_name" to userName,
                        "user_id" to userId,
                        "user_icon_url" to profileUrl,
                        "like_count" to likeCount
                    )
                    findNavController().navigate(R.id.action_to_dialog_image_preview, bundle)
                }

                override fun onLikeClick(tweetId: Long, isLiked: Boolean) {
                    tweetsViewModel.likeTweet(tweetId, isLiked)
                    updateTweetInAdapter(tweetId) {
                        it.isLiked = isLiked
                        it.likesCount = if (isLiked) it.likesCount+1 else it.likesCount-1
                    }
                }

                override fun onCommentClick(tweetId: Long) {
                    val action = AppNavigationDirections.actionToFragmentUserPost(tweetId)
                    NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
                }

                override fun onSaveClick(tweetId: Long, isSaved: Boolean) {
                    tweetsViewModel.bookMarkTweet(tweetId, isSaved)
                    updateTweetInAdapter(tweetId) {
                        it.isBookMarked = isSaved
                    }
                }

                override fun onShareClick(tweetId: Long) {
                    val action = AppNavigationDirections.actionToShareBottomSheetFragment(tweetId)
                    findNavController().navigate(action)
                }

                override fun onReportClick(tweetId: Long) {
                    val action= AppNavigationDirections.actionToDialogSubmitAReport(isPost=true, targetId =tweetId)
                    findNavController().navigate(action)
                }

                override fun onDeleteClick(tweetId: Long) {
                    tweetsViewModel.deleteTweet(tweetId) {deleted->
                        if(deleted){
                            tweetsAdapter.refresh()
                        }else{
                            Toast.makeText(requireContext(),"Unable to delete tweet", Toast.LENGTH_LONG).show()
                        }
                    }
                }

                override fun onEditClick(tweet: Tweet) {
                    val editDialog = EditTweetDialog.newInstance(tweet) { updatedTweet ->
                        updateTweetInAdapter(updatedTweet.id) { tweetInAdapter ->
                            tweetInAdapter.text = updatedTweet.text
                            tweetInAdapter.mediaCount = updatedTweet.mediaCount
                            tweetInAdapter.media = updatedTweet.media
                            tweetInAdapter.editedAt = updatedTweet.editedAt
                            tweetInAdapter.isEdited = updatedTweet.isEdited
                        }
                        tweetsAdapter.notifyDataSetChanged()
                    }
                    editDialog.show(parentFragmentManager, "EditTweetDialog")
                }
            }
        )
    }

    private fun updateTweetInAdapter(tweetId: Long, update: (Tweet) -> Unit) {
        val index = tweetsAdapter.snapshot().items.indexOfFirst { it.id == tweetId }
        val tweet = tweetsAdapter.peek(index)
        if (tweet != null) {
            update(tweet)
        }
    }
}
