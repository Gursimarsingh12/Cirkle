package com.app.cirkle.presentation.features.create

import android.util.Log
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.Toast
import androidx.fragment.app.activityViewModels
import androidx.fragment.app.setFragmentResultListener
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.bumptech.glide.Glide
import com.bumptech.glide.load.engine.DiskCacheStrategy
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.core.utils.common.NavUtils
import com.app.cirkle.databinding.FragmentCreateBinding
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.common.SharedImageViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@AndroidEntryPoint
class CreateFragment : BaseFragment<FragmentCreateBinding>() {

    private val viewModel: CreatePostViewModel by viewModels()
    private val imageViewModel: SharedImageViewModel by activityViewModels()
    @Inject
    lateinit var imageUtils: ImageUtils

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentCreateBinding {
        return FragmentCreateBinding.inflate(inflater, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.linearLayout.handleBottomInset()
        // Observe UI state
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.uiState.collect { uiState ->
                        handleUiState(uiState)
                    }
                }
                launch {
                    imageViewModel.createFragmentImageFiles.collect { files ->
                        updateImagePreviewUI(files)
                        binding.textPostHint.setText(imageViewModel.text)
                    }
                }
            }
        }

        setUpResultListener()
        setupListeners()
    }

    private fun setUpResultListener(){
        setFragmentResultListener("camera_result") { _, bundle ->
            val filePath = bundle.getString("image_file_path")
            val file = filePath?.let { File(it) }

            if (file != null) {
                imageViewModel.addImage(file)
            }
        }
    }

    private fun setupListeners() {
        binding.btnPost.setOnClickListener {
            val postText = binding.textPostHint.text.toString()
            if (postText.isNotBlank()) {
                val images=imageViewModel.createFragmentImageFiles.value
                if(images.isNotEmpty())
                    viewModel.postTweet(postText,images)
                else
                    viewModel.postTweet(postText,mutableListOf<File>())
            } else {
                Toast.makeText(
                    requireContext(),
                    "Please enter text to post.",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }

        binding.btnAttachImage.setOnClickListener {
            if(binding.textPostHint.text.toString().isNotBlank()){
                imageViewModel.text=binding.textPostHint.text.toString()
            }
            val action= CreateFragmentDirections.actionFragmentCreateToFragmentCamera(false,false)
            NavUtils.navigateWithSlideAnimAndPopUpTo(findNavController(), action.actionId, R.id.fragment_create, false, action.arguments)
        }
    }

    private fun updateImagePreviewUI(files: List<File>) {
        Log.d("Image","${files.size} and $files")
        binding.imageOneOneContainer.visibility = View.GONE
        binding.twoImageContainer.visibility = View.GONE
        binding.threeImageContainer.visibility = View.GONE
        binding.fourImageContainer.visibility = View.GONE
        binding.removeImageOneOne.visibility = View.GONE
        binding.removeImageTwoOne.visibility = View.GONE
        binding.removeImageTwoTwo.visibility = View.GONE
        binding.removeImageThreeOne.visibility = View.GONE
        binding.removeImageThreeTwo.visibility = View.GONE
        binding.removeImageThreeThree.visibility = View.GONE
        binding.removeImageFourOne.visibility = View.GONE
        binding.removeImageFourTwo.visibility = View.GONE
        binding.removeImageFourThree.visibility = View.GONE
        binding.removeImageFourFour.visibility = View.GONE

        when(files.size) {
            1 -> {
                binding.imageOneOneContainer.visibility = View.VISIBLE
                loadImage(binding.imageOneOne, files[0])
                binding.removeImageOneOne.visibility = View.VISIBLE
                binding.removeImageOneOne.setOnClickListener { imageViewModel.removeImage(0) }
            }
            2 -> {
                binding.twoImageContainer.visibility = View.VISIBLE
                loadImage(binding.imageTwoOne, files[0])
                loadImage(binding.imageTwoTwo, files[1])
                binding.removeImageTwoOne.visibility = View.VISIBLE
                binding.removeImageTwoTwo.visibility = View.VISIBLE
                binding.removeImageTwoOne.setOnClickListener { imageViewModel.removeImage(0) }
                binding.removeImageTwoTwo.setOnClickListener { imageViewModel.removeImage(1) }
            }
            3 -> {
                binding.threeImageContainer.visibility = View.VISIBLE
                loadImage(binding.imageThreeOne, files[0])
                loadImage(binding.imageThreeTwo, files[1])
                loadImage(binding.imageThreeThree, files[2])
                binding.removeImageThreeOne.visibility = View.VISIBLE
                binding.removeImageThreeTwo.visibility = View.VISIBLE
                binding.removeImageThreeThree.visibility = View.VISIBLE
                binding.removeImageThreeOne.setOnClickListener { imageViewModel.removeImage(0) }
                binding.removeImageThreeTwo.setOnClickListener { imageViewModel.removeImage(1) }
                binding.removeImageThreeThree.setOnClickListener { imageViewModel.removeImage(2) }
            }
            4 -> {
                binding.fourImageContainer.visibility = View.VISIBLE
                loadImage(binding.imageFourOne, files[0])
                loadImage(binding.imageFourTwo, files[1])
                loadImage(binding.imageFourThree, files[2])
                loadImage(binding.imageFourFour, files[3])
                binding.removeImageFourOne.visibility = View.VISIBLE
                binding.removeImageFourTwo.visibility = View.VISIBLE
                binding.removeImageFourThree.visibility = View.VISIBLE
                binding.removeImageFourFour.visibility = View.VISIBLE
                binding.removeImageFourOne.setOnClickListener { imageViewModel.removeImage(0) }
                binding.removeImageFourTwo.setOnClickListener { imageViewModel.removeImage(1) }
                binding.removeImageFourThree.setOnClickListener { imageViewModel.removeImage(2) }
                binding.removeImageFourFour.setOnClickListener { imageViewModel.removeImage(3) }
            }
            else -> {
                // Hide all
            }
        }
    }


    private fun handleUiState(uiState: CreatePostUiState) {
        when (uiState) {
            is CreatePostUiState.Loading -> {
                showLoading()
            }

            is CreatePostUiState.Success -> {
                hideLoading()
                binding.textName.visibility = View.VISIBLE
                binding.textUserId.visibility = View.VISIBLE
                val user = uiState.myProfile
                imageUtils.loadImageIntoImageView(user.profileUrl,binding.imageAvatar, centerCrop = true, cacheImage = true)
                binding.textName.text = user.name
                binding.textUserId.text = "ID: ${user.id}"
                binding.checkMark.setAccountType(user.checkMarkState)
            }

            is CreatePostUiState.PostSuccess -> {
                hideLoading()
                Toast.makeText(
                    requireContext(),
                    "Post successful: ${uiState.message}",
                    Toast.LENGTH_SHORT
                ).show()
                binding.textPostHint.text.clear()
                imageViewModel.clear()
                val action = CreateFragmentDirections.actionFragmentCreateToFragmentMyProfile()
                NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
            }

            is CreatePostUiState.Error -> {
                hideLoading()
                binding.textName.visibility = View.GONE
                binding.textUserId.visibility = View.GONE
                Log.d("BackEnd",uiState.message.toString())

                Toast.makeText(requireContext(), uiState.message, Toast.LENGTH_LONG).show()
            }

            CreatePostUiState.Idle -> {
                hideLoading()
            }
        }
    }
    private fun loadImage(view: ImageView, file: File) {
        Glide.with(view.context)
            .load(file)
            .centerCrop()
            .diskCacheStrategy(DiskCacheStrategy.DATA)
            .into(view)
    }
}