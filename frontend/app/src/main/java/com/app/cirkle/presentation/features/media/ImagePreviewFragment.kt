package com.app.cirkle.presentation.features.media

import android.graphics.Bitmap
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.os.bundleOf
import androidx.fragment.app.activityViewModels
import androidx.fragment.app.setFragmentResult
import androidx.navigation.fragment.findNavController
import androidx.navigation.fragment.navArgs
import com.app.cirkle.core.components.CropImageView
import com.app.cirkle.databinding.FragmentPreviewClickedImageBinding
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.common.SharedImageViewModel
import com.app.cirkle.core.utils.common.NavUtils
import dagger.hilt.android.AndroidEntryPoint
import java.io.File
import java.io.FileOutputStream

@AndroidEntryPoint
class ImagePreviewFragment : BaseFragment<FragmentPreviewClickedImageBinding>() {

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentPreviewClickedImageBinding {
        return FragmentPreviewClickedImageBinding.inflate(inflater)
    }

    private val navArgs: ImagePreviewFragmentArgs by navArgs()
    private val sharedImageViewModel: SharedImageViewModel by activityViewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setUpViews()
        binding.root.handleAllInsets()
        binding.buttonContainer.handleBottomInset()
        val image = sharedImageViewModel.capturedImage.value
        binding.imageToCrop.setImageBitmap(image)
    }

    private fun setUpViews() {
        if(navArgs.isCircle){
            binding.orientation.visibility= View.GONE
            binding.imageToCrop.cropMode= CropImageView.CropMode.CIRCLE
        }else{
            binding.orientation.visibility= View.VISIBLE
            binding.imageToCrop.cropMode= CropImageView.CropMode.RECTANGLE_PORTRAIT
        }

        binding.orientation.setOnStateChangeListener { isLandScape->
            if(isLandScape){
                binding.imageToCrop.cropMode= CropImageView.CropMode.RECTANGLE_LANDSCAPE
            }else{
                binding.imageToCrop.cropMode= CropImageView.CropMode.RECTANGLE_PORTRAIT
            }
        }

        binding.btnCrop.setOnClickListener {
            binding.finalImagePreview.visibility = View.VISIBLE
            binding.cropViewContainer.visibility = View.GONE

            val bitmap = binding.imageToCrop.getCroppedBitmap()
            binding.finalImagePreview.setImageBitmap(bitmap)

            // Save bitmap to a temp file
            val file = saveBitmapToCache(bitmap!!)

            // Set fragment result with file path
            setFragmentResult(
                "camera_result",
                bundleOf("image_file_path" to file.absolutePath,
                    "is_profile" to navArgs.isCircle)
            )

            val action = when {
                navArgs.isFromEditTweet -> 
                    ImagePreviewFragmentDirections.actionFragmentClickPreviewToFragmentMyProfile()
                navArgs.isFromProfile -> 
                    ImagePreviewFragmentDirections.actionFragmentClickPreviewToFragmentEditProfile()
                else -> 
                    ImagePreviewFragmentDirections.actionFragmentClickPreviewToFragmentCreatePost()
            }
            // Navigate back
            NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
        }
        binding.btnCancel.setOnClickListener {
            findNavController().navigateUp()
        }
    }

    private fun saveBitmapToCache(bitmap: Bitmap): File {
        val fileName = "CROPPED_${System.currentTimeMillis()}.jpg"
        val file = File(requireContext().cacheDir, fileName)

        FileOutputStream(file).use { out ->
            bitmap.compress(Bitmap.CompressFormat.JPEG, 90, out)
        }

        return file
    }


}