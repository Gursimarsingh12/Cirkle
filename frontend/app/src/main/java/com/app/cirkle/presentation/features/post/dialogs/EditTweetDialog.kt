package com.app.cirkle.presentation.features.post.dialogs

import android.app.Dialog
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.ImageView
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.core.os.bundleOf
import androidx.fragment.app.DialogFragment
import androidx.fragment.app.activityViewModels
import androidx.fragment.app.setFragmentResult
import androidx.fragment.app.setFragmentResultListener
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.bumptech.glide.Glide
import com.bumptech.glide.load.engine.DiskCacheStrategy
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.core.utils.common.DialogUtils
import com.app.cirkle.core.utils.validation.TweetInputValidator
import com.app.cirkle.databinding.DialogEditTweetBinding
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.presentation.common.SharedImageViewModel
import com.app.cirkle.presentation.features.post.EditTweetImage
import com.app.cirkle.presentation.features.post.EditTweetImageAdapter
import com.app.cirkle.presentation.features.post.viewmodels.EditTweetUiState
import com.app.cirkle.presentation.features.post.viewmodels.EditTweetViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@AndroidEntryPoint
class EditTweetDialog : DialogFragment() {

    private var _binding: DialogEditTweetBinding? = null
    private val binding get() = _binding!!

    private val viewModel: EditTweetViewModel by viewModels()
    private val imageViewModel: SharedImageViewModel by activityViewModels()

    private var tweet: Tweet? = null
    private var onTweetUpdated: ((Tweet) -> Unit)? = null

    private val images = mutableListOf<EditTweetImage>()
    private val removedUrls = mutableSetOf<String>() // Track removed existing images
    private lateinit var imageAdapter: EditTweetImageAdapter

    @Inject
    lateinit var imageUtils: ImageUtils

    companion object {
        fun newInstance(tweet: Tweet, onTweetUpdated: (Tweet) -> Unit): EditTweetDialog {
            return EditTweetDialog().apply {
                this.tweet = tweet
                this.onTweetUpdated = onTweetUpdated
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        tweet?.let { tweet ->
            if (imageViewModel.text.isEmpty()) {
                imageViewModel.text = tweet.text
            }
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = DialogEditTweetBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        if (imageViewModel.pendingEditTweet.value == null) {
            imageViewModel.clear()
        }
        setupImageRecycler()
        setupUI()
        setupObservers()
        setupListeners()
        setupResultListeners()
        
        view.post {
            refreshImages()
            updateSaveButtonState(binding.editTextTweet.text.toString())
        }
    }

    override fun onCreateDialog(savedInstanceState: Bundle?): Dialog {
        val dialog = super.onCreateDialog(savedInstanceState)
        dialog.window?.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        dialog.window?.setLayout(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        )
        return dialog
    }

    override fun onStart() {
        super.onStart()
        DialogUtils.setCompactWidth(dialog, resources)
    }

    override fun onResume() {
        super.onResume()
        refreshImages()
        updateSaveButtonState(binding.editTextTweet.text.toString())
    }

    private fun refreshImages() {
        tweet?.let { tweet ->
            val oldImages = images.toList()
            images.clear()
            tweet.media.forEach { if (!removedUrls.contains(it.url)) images.add(EditTweetImage.Existing(it.url)) }
            val newFiles = imageViewModel.createFragmentImageFiles.value
            newFiles.forEach { file ->
                if (images.size < 4) {
                    images.add(EditTweetImage.New(file))
                }
            }
            val hasChanged = oldImages.size != images.size || 
                oldImages.zip(images).any { (old, new) -> 
                    when {
                        old is EditTweetImage.Existing && new is EditTweetImage.Existing -> old.url != new.url
                        old is EditTweetImage.New && new is EditTweetImage.New -> old.file != new.file
                        else -> true
                    }
                }
            if (hasChanged) {
                imageAdapter.notifyDataSetChanged()
            }
            updateImageUI()
        }
    }

    private fun setupImageRecycler() {
        imageAdapter = EditTweetImageAdapter(images, { position ->
            val removed = images.removeAt(position)
            if (removed is EditTweetImage.Existing) {
                removedUrls.add(removed.url)
            } else if (removed is EditTweetImage.New) {
                // Remove the file from imageViewModel.createFragmentImageFiles
                val currentFiles = imageViewModel.createFragmentImageFiles.value.toMutableList()
                currentFiles.remove(removed.file)
                imageViewModel.setCreateFragmentImages(currentFiles)
            }
            imageAdapter.notifyItemRemoved(position)
            refreshImages()
            updateSaveButtonState(binding.editTextTweet.text.toString())
        }, imageUtils)
        binding.recyclerViewImages.apply {
            layoutManager =
                LinearLayoutManager(requireContext(), LinearLayoutManager.HORIZONTAL, false)
            adapter = imageAdapter
        }
    }

    private fun setupUI() {
        tweet?.let { tweet ->
            val text = if (imageViewModel.text.isNotEmpty() && imageViewModel.text != tweet.text) {
                imageViewModel.text
            } else {
                tweet.text
            }
            binding.editTextTweet.setText(text)
            binding.editTextTweet.setSelection(text.length)
            updateCharacterCount(text)
            images.clear()
            removedUrls.clear() // Reset removed URLs on setup
            tweet.media.forEach { images.add(EditTweetImage.Existing(it.url)) }
            val newFiles = imageViewModel.createFragmentImageFiles.value
            newFiles.forEach { file ->
                if (images.size < 4) {
                    images.add(EditTweetImage.New(file))
                }
            }
            imageAdapter.notifyDataSetChanged()
            updateImageUI()
        }
    }

    private fun updateImageUI() {
        binding.recyclerViewImages.visibility = if (images.isNotEmpty()) View.VISIBLE else View.GONE
        binding.buttonRemoveAllImages.visibility = if (images.isNotEmpty()) View.VISIBLE else View.GONE
        binding.buttonAddImage.visibility = if (images.size < 4) View.VISIBLE else View.GONE
    }

    private fun setupObservers() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.uiState.collect { uiState ->
                        handleUiState(uiState)
                    }
                }
                launch {
                    imageViewModel.createFragmentImageFiles.collect { files ->
                        refreshImages()
                        updateImagePreviewUI(files)
                        if (binding.editTextTweet.text.toString() != imageViewModel.text && imageViewModel.text.isNotEmpty()) {
                            binding.editTextTweet.setText(imageViewModel.text)
                            binding.editTextTweet.setSelection(imageViewModel.text.length)
                        }
                        updateSaveButtonState(binding.editTextTweet.text.toString())
                    }
                }
            }
        }
    }

    private fun setupResultListeners() {
        setFragmentResultListener("camera_result") { _, bundle ->
            val filePath = bundle.getString("image_file_path")
            val file = filePath?.let { File(it) }
            if (file != null && images.size < 4) {
                images.add(EditTweetImage.New(file))
                imageAdapter.notifyItemInserted(images.lastIndex)
                updateImageUI()
                updateSaveButtonState(binding.editTextTweet.text.toString())
            }
        }
    }

    private fun setupListeners() {
        binding.editTextTweet.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                val text = s?.toString() ?: ""
                updateCharacterCount(text)
                updateSaveButtonState(text)
            }
        })

        binding.buttonClose.setOnClickListener {
            imageViewModel.clearPendingEditTweet()
            imageViewModel.clear()
            dismiss()
        }

        binding.buttonCancel.setOnClickListener {
            imageViewModel.clearPendingEditTweet()
            imageViewModel.clear()
            dismiss()
        }

        binding.buttonSave.setOnClickListener {
            val text = binding.editTextTweet.text.toString().trim()
            val validationError = TweetInputValidator.getTweetValidationError(text)
            if (validationError != null) {
                Toast.makeText(requireContext(), validationError, Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            tweet?.let { tweet ->
                // Build correct lists for update
                val keptExistingUrls = tweet.media.map { it.url }.filter { !removedUrls.contains(it) }
                val newFiles = images.filterIsInstance<EditTweetImage.New>().map { it.file }
                viewModel.editTweet(tweet.id, text, keptExistingUrls, newFiles)
            }
        }

        binding.buttonAddImage.setOnClickListener {
            if (images.size < 4) {
                navigateToCamera()
            }
        }

        binding.buttonRemoveAllImages.setOnClickListener {
            images.clear()
            imageAdapter.notifyDataSetChanged()
            updateImageUI()
            updateSaveButtonState(binding.editTextTweet.text.toString())
        }
    }

    private fun navigateToCamera() {
        imageViewModel.text = binding.editTextTweet.text.toString()
        val newFiles = images.filterIsInstance<EditTweetImage.New>().map { it.file }
        imageViewModel.setCreateFragmentImages(newFiles)
        
        tweet?.let { tweetToEdit ->
            onTweetUpdated?.let { callback ->
                imageViewModel.setPendingEditTweet(tweetToEdit, callback)
            }
        }
        
        setFragmentResult("edit_tweet_camera_request", bundleOf())
        dismiss()
    }

    private fun updateCharacterCount(text: String) {
        val remaining = TweetInputValidator.getTweetRemainingChars(text)
        binding.textCharacterCount.text = "$remaining characters remaining"

        when {
            remaining < 0 -> {
                binding.textCharacterCount.setTextColor(
                    ContextCompat.getColor(requireContext(), R.color.red)
                )
            }
            remaining < 50 -> {
                binding.textCharacterCount.setTextColor(
                    ContextCompat.getColor(requireContext(), R.color.orange)
                )
            }
            else -> {
                binding.textCharacterCount.setTextColor(
                    ContextCompat.getColor(requireContext(), R.color.iconbgnotactive)
                )
            }
        }
    }

    private fun updateSaveButtonState(text: String) {
        val isValid = TweetInputValidator.isValidTweetText(text)
        
        val originalMediaCount = tweet?.media?.size ?: 0
        val currentExistingImages = images.filterIsInstance<EditTweetImage.Existing>().size
        val currentNewImages = images.filterIsInstance<EditTweetImage.New>().size
        
        val textChanged = text.trim() != tweet?.text
        val imagesChanged = currentExistingImages != originalMediaCount || currentNewImages > 0
        val hasChanged = textChanged || imagesChanged

        binding.buttonSave.isEnabled = isValid && hasChanged
        binding.buttonSave.alpha = if (isValid && hasChanged) 1.0f else 0.5f
    }

    private fun updateImagePreviewUI(files: List<File>) {
        updateSaveButtonState(binding.editTextTweet.text.toString())
    }

    private fun loadImage(view: ImageView, file: File) {
        Glide.with(view.context)
            .load(file)
            .centerCrop()
            .diskCacheStrategy(DiskCacheStrategy.DATA)
            .into(view)
    }

    private fun handleUiState(uiState: EditTweetUiState) {
        when (uiState) {
            is EditTweetUiState.Loading -> {
                binding.progressBar.visibility = View.VISIBLE
                binding.buttonSave.isEnabled = false
            }
            is EditTweetUiState.Success -> {
                binding.progressBar.visibility = View.GONE
                imageViewModel.clearPendingEditTweet()
                imageViewModel.clear()
                onTweetUpdated?.invoke(uiState.tweet)
                dismiss()
            }
            is EditTweetUiState.Error -> {
                binding.progressBar.visibility = View.GONE
                binding.buttonSave.isEnabled = true
                Toast.makeText(requireContext(), uiState.message, Toast.LENGTH_SHORT).show()
            }
            EditTweetUiState.Idle -> {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        if (imageViewModel.pendingEditTweet.value == null) {
            imageViewModel.clear()
        }
        _binding = null
    }
}