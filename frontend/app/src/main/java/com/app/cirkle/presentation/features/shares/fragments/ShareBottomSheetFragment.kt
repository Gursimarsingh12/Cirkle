package com.app.cirkle.presentation.features.shares.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.navArgs
import androidx.paging.LoadState
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.R
import com.google.android.material.bottomsheet.BottomSheetBehavior
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyBottomInset
import com.app.cirkle.databinding.BottomSheetShareBinding
import com.app.cirkle.presentation.common.Resource
import com.app.cirkle.presentation.features.shares.adapters.MyFollowingAdapter
import com.app.cirkle.presentation.features.shares.viewmodels.ShareViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class ShareBottomSheetFragment : BottomSheetDialogFragment() {

    private var _binding: BottomSheetShareBinding? = null
    private val binding get() = _binding!!

    private val viewModel: ShareViewModel by viewModels()
    private lateinit var myFollowingAdapter: MyFollowingAdapter
    private val args: ShareBottomSheetFragmentArgs by navArgs()

    @Inject
    lateinit var imageUtils: ImageUtils

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = BottomSheetShareBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        requireDialog().setOnShowListener { dialog ->
            val bottomSheetView = (dialog as BottomSheetDialog)
                .findViewById<View>(R.id.design_bottom_sheet)
            bottomSheetView?.let { sheet ->
                val behavior = BottomSheetBehavior.from(sheet)
                behavior.state = BottomSheetBehavior.STATE_EXPANDED
                behavior.skipCollapsed = true
                behavior.peekHeight = 0

                // Fixed height ~80% screen
                val params = sheet.layoutParams
                params.height = (resources.displayMetrics.heightPixels*0.85).toInt()
                sheet.layoutParams = params
            }
        }
        binding.root.applyBottomInset()
        binding.btnShare.isEnabled = false
        binding.btnShare.alpha = 0.5f
        binding.tvShareHeader.visibility = View.VISIBLE
        binding.tvShareHeader.text = "Share with mutual followers"
        setupRecyclerView()
        observeViewModel()
        binding.emptyMutualFollowersView.visibility = View.GONE
    }

    private fun setupRecyclerView() {
        myFollowingAdapter = MyFollowingAdapter(
            imageUtils = imageUtils,
        ) { selectedUsers ->
            viewModel.updateSelectedUsers(selectedUsers)
        }

        binding.rvUsers.apply {
            adapter = myFollowingAdapter
            layoutManager = LinearLayoutManager(requireContext())
        }

        binding.btnShare.setOnClickListener {
            viewModel.shareTweet(args.tweetId, "Check out this post!")
        }

        myFollowingAdapter.addLoadStateListener { loadState ->
            val isListEmpty =
                loadState.refresh is LoadState.NotLoading &&
                myFollowingAdapter.itemCount == 0 &&
                loadState.append.endOfPaginationReached

            binding.emptyMutualFollowersView.visibility = if (isListEmpty) View.VISIBLE else View.GONE
            binding.rvUsers.visibility = if (isListEmpty) View.GONE else View.VISIBLE
            binding.btnShare.visibility = if (isListEmpty) View.GONE else View.VISIBLE

            binding.progressBar.visibility = if (loadState.refresh is LoadState.Loading) View.VISIBLE else View.GONE
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.pagedMutualFollowers.collectLatest { pagingData ->
                        myFollowingAdapter.submitData(pagingData)
                    }
                }

                launch {
                    viewModel.shareStatus.collect { resource ->
                        when (resource) {
                            is Resource.Loading -> {
                                binding.progressBar.visibility = View.VISIBLE
                                binding.btnShare.isEnabled = false
                            }
                            is Resource.Success -> {
                                binding.progressBar.visibility = View.GONE
                                binding.btnShare.isEnabled = true
                                Toast.makeText(context, "Post shared successfully", Toast.LENGTH_SHORT).show()
                                dismiss()
                            }
                            is Resource.Error -> {
                                binding.progressBar.visibility = View.GONE
                                binding.btnShare.isEnabled = true
                                Toast.makeText(context, resource.message, Toast.LENGTH_SHORT).show()
                            }
                            else -> {
                                binding.progressBar.visibility = View.GONE
                            }
                        }
                    }
                }

                launch {
                    viewModel.isShareButtonEnabled.collect { isEnabled ->
                        binding.btnShare.isEnabled = isEnabled
                        binding.btnShare.alpha = if (isEnabled) 1.0f else 0.5f
                    }
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
