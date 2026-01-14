package com.app.cirkle.presentation.features.post.base

import android.widget.Toast
import androidx.fragment.app.viewModels
import androidx.navigation.fragment.findNavController
import androidx.viewbinding.ViewBinding
import com.app.cirkle.AppNavigationDirections
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.core.utils.common.NavUtils
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.features.post.common.CommentsAdapter
import com.app.cirkle.presentation.features.post.dialogs.EditCommentDialog
import com.app.cirkle.presentation.features.post.fragments.PostFragmentDirections
import com.app.cirkle.presentation.features.tweets.TweetsViewModel
import javax.inject.Inject
import kotlin.getValue

abstract class BaseCommentFragment<VB: ViewBinding>: BaseFragment<VB>() {

    override fun shouldApplyBottomInset(): Boolean = true

    @Inject
    lateinit var imageUtils: ImageUtils
    private val viewModel: CommentViewModel by viewModels()

    protected val commentsAdapter: CommentsAdapter by lazy {
        CommentsAdapter(
            viewModel.getUserId(),
            imageUtils,
            object : CommentsAdapter.ClickListener {
                override fun onLikeClick(id: Long, isLiked: Boolean) {
                    viewModel.likeComment(id, isLiked)
                    val index = commentsAdapter.snapshot().items.indexOfFirst { it.commentId == id }
                    if (index != -1) {
                        val item = commentsAdapter.peek(index)
                        if (item != null) {
                            item.isLikedByUser = isLiked
                            item.commentLikesCount += if (isLiked) 1 else -1
                            commentsAdapter.notifyItemChanged(index)
                        }
                    }
                }

                override fun onRepliesClick(comment: Comment) {
                    val action =
                        PostFragmentDirections.actionFromFragmentPostToFragmentCommentReplies(
                            comment
                        )
                    NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
                }

                override fun onProfileClick(userId: String) {
                    val action = PostFragmentDirections.actionToFragmentUserProfile(userId)
                    NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
                }

                override fun onDeleteClick(commentId: Long) {
                    viewModel.deleteComment(commentId) { done ->
                        if (done) {
                            commentsAdapter.refresh()
                            Toast.makeText(requireContext(),"Comment deleted!", Toast.LENGTH_SHORT).show()
                        } else {
                            Toast.makeText(
                                requireContext(),
                                "Unable to delete the comment. Try Again!",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    }
                }

                override fun onReportClick(commentId: Long) {
                    val action =
                        AppNavigationDirections.actionToDialogSubmitAReport(isPost=false, targetId = commentId)
                    NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
                }

                override fun onEditClick(comment: Comment) {
                    val editDialog = EditCommentDialog.newInstance(comment) { updatedComment ->
                        val index = commentsAdapter.snapshot().items.indexOfFirst { it.commentId == updatedComment.commentId }
                        val commentInAdapter = commentsAdapter.peek(index)
                        if (commentInAdapter != null) {
                            commentInAdapter.text = updatedComment.text
                            commentInAdapter.editedAt = updatedComment.editedAt
                            commentInAdapter.isEdited = updatedComment.isEdited
                            commentsAdapter.notifyItemChanged(index)
                        }
                    }
                    editDialog.show(parentFragmentManager, "EditCommentDialog")
                }

            })
    }
}