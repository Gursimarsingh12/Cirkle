package com.app.cirkle.presentation.features.myprofile.dialog

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.paging.PagingData
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.domain.model.user.MyFollowFollowing
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject
import android.widget.TextView
import com.app.cirkle.R
import android.widget.LinearLayout
import android.widget.ImageView

@AndroidEntryPoint
abstract class BaseFollowFragment : Fragment() {

    protected abstract val dataFlow: Flow<PagingData<MyFollowFollowing>>

    @Inject
    lateinit var imageUtils: ImageUtils

    protected open val showUnfollow: Boolean = false
    protected open val onUnfollow: ((MyFollowFollowing) -> Unit)? = null

    protected lateinit var adapter: FollowAdapter

    private lateinit var recyclerView: RecyclerView
    private lateinit var emptyView: LinearLayout
    private lateinit var emptyIcon: ImageView
    private lateinit var emptyTitle: TextView
    private lateinit var emptySubtitle: TextView

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_follow_dialog, container, false)
        recyclerView = view.findViewById(R.id.recycleView)
        emptyView = view.findViewById(R.id.emptyView)
        emptyIcon = view.findViewById(R.id.emptyIcon)
        emptyTitle = view.findViewById(R.id.emptyTitle)
        emptySubtitle = view.findViewById(R.id.emptySubtitle)
        return view
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        adapter = createAdapter(imageUtils)
        recyclerView.adapter = adapter

        // Set emptyView content based on fragment type
        if (this@BaseFollowFragment is FollowersFragment) {
            emptyIcon.setImageResource(R.drawable.ic_launcher_foreground)
            emptyTitle.text = "No one is following you yet"
            emptySubtitle.text = "When someone follows you, they will appear here!"
        } else {
            emptyIcon.setImageResource(R.drawable.ic_launcher_foreground)
            emptyTitle.text = "You are not following anyone yet"
            emptySubtitle.text = "Start following people to see them here!"
        }

        viewLifecycleOwner.lifecycleScope.launch {
            dataFlow.collectLatest {
                adapter.submitData(it)
            }
        }
        adapter.registerAdapterDataObserver(object : RecyclerView.AdapterDataObserver() {
            override fun onChanged() = checkEmptyState()
            override fun onItemRangeInserted(positionStart: Int, itemCount: Int) = checkEmptyState()
            override fun onItemRangeRemoved(positionStart: Int, itemCount: Int) = checkEmptyState()
        })
        checkEmptyState()
    }

    private fun checkEmptyState() {
        val isEmpty = adapter.itemCount == 0
        recyclerView.visibility = if (isEmpty) View.GONE else View.VISIBLE
        emptyView.visibility = if (isEmpty) View.VISIBLE else View.GONE
    }

    // Let subclass customize how adapter is created if needed
    protected open fun createAdapter(imageUtils: ImageUtils): FollowAdapter {
        return FollowAdapter(imageUtils, showUnfollow, onUnfollow)
    }
}

