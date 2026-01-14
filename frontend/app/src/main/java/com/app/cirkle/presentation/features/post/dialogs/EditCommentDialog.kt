package com.app.cirkle.presentation.features.post.dialogs

import android.app.Dialog
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.fragment.app.DialogFragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.app.cirkle.R
import com.app.cirkle.core.utils.validation.TweetInputValidator
import com.app.cirkle.databinding.DialogEditCommentBinding
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.presentation.features.post.viewmodels.EditCommentUiState
import com.app.cirkle.presentation.features.post.viewmodels.EditCommentViewModel
import com.app.cirkle.core.utils.common.DialogUtils
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class EditCommentDialog : DialogFragment() {

    private var _binding: DialogEditCommentBinding? = null
    private val binding get() = _binding!!

    private val viewModel: EditCommentViewModel by viewModels()

    private var comment: Comment? = null
    private var onCommentUpdated: ((Comment) -> Unit)? = null

    companion object {
        fun newInstance(comment: Comment, onCommentUpdated: (Comment) -> Unit): EditCommentDialog {
            return EditCommentDialog().apply {
                this.comment = comment
                this.onCommentUpdated = onCommentUpdated
            }
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = DialogEditCommentBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupUI()
        setupObservers()
        setupListeners()
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

    private fun setupUI() {
        comment?.let { comment ->
            binding.editTextComment.setText(comment.text)
            binding.editTextComment.setSelection(comment.text.length)
            updateCharacterCount(comment.text)
        }
    }

    private fun setupObservers() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { uiState ->
                    handleUiState(uiState)
                }
            }
        }
    }

    private fun setupListeners() {
        binding.editTextComment.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                val text = s?.toString() ?: ""
                updateCharacterCount(text)
                updateSaveButtonState(text)
            }
        })

        binding.buttonClose.setOnClickListener {
            dismiss()
        }

        binding.buttonCancel.setOnClickListener {
            dismiss()
        }

        binding.buttonSave.setOnClickListener {
            val text = binding.editTextComment.text.toString().trim()
            val validationError = TweetInputValidator.getCommentValidationError(text)

            if (validationError != null) {
                Toast.makeText(requireContext(), validationError, Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            comment?.let { comment ->
                if (text != comment.text) {
                    viewModel.editComment(comment.commentId, text)
                } else {
                    dismiss()
                }
            }
        }
    }

    private fun updateCharacterCount(text: String) {
        val remaining = TweetInputValidator.getCommentRemainingChars(text)
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
        val isValid = TweetInputValidator.isValidCommentText(text)
        val hasChanged = text.trim() != comment?.text

        binding.buttonSave.isEnabled = isValid && hasChanged
        binding.buttonSave.alpha = if (isValid && hasChanged) 1.0f else 0.5f
    }

    private fun handleUiState(uiState: EditCommentUiState) {
        when (uiState) {
            is EditCommentUiState.Loading -> {
                binding.progressBar.visibility = View.VISIBLE
                binding.buttonSave.isEnabled = false
            }
            is EditCommentUiState.Success -> {
                binding.progressBar.visibility = View.GONE
                onCommentUpdated?.invoke(uiState.comment)
                dismiss()
            }
            is EditCommentUiState.Error -> {
                binding.progressBar.visibility = View.GONE
                binding.buttonSave.isEnabled = true
                Toast.makeText(requireContext(), uiState.message, Toast.LENGTH_SHORT).show()
            }
            EditCommentUiState.Idle -> {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}