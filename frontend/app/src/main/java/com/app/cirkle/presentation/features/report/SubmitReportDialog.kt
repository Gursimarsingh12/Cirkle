package com.app.cirkle.presentation.features.report

import android.os.Bundle
import androidx.fragment.app.DialogFragment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.view.isVisible
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.navArgs
import com.app.cirkle.R
import com.app.cirkle.databinding.DialogSubmitReportBinding
import com.app.cirkle.presentation.common.Resource
import com.app.cirkle.core.utils.common.DialogUtils
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class SubmitReportDialog : DialogFragment() {

    private var _binding: DialogSubmitReportBinding?=null
    private val binding: DialogSubmitReportBinding
        get()=_binding!!

    private val navArgs: SubmitReportDialogArgs by navArgs()
    private val viewModel: SubmitReportViewModel by viewModels()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        _binding= DialogSubmitReportBinding.inflate(inflater)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        isCancelable = true

        setupUI()
        setupListeners()
        observeUiState()
    }

    private fun setupUI() {
        val isPost = navArgs.isPost
        binding.subtitleText.text = if (isPost) "Report a post" else "Report a comment"
    }

    private fun setupListeners() {
        binding.cancelButton.setOnClickListener {
            dismiss()
        }

        binding.submitButton.setOnClickListener {
            val text = binding.reportEditText.text.toString().trim()
            if (text.isNotEmpty()) {
                hideError()
                viewModel.report(
                    navArgs.targetId,
                    text,
                    navArgs.isPost
                )
            } else {
                // Optional: show a toast or error
                showError("Please enter a reason")
            }
        }
    }

    private fun observeUiState() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    when (state) {
                        is Resource.Loading -> {
                            showLoadingState(true)
                        }
                        is Resource.Success -> {
                            dismiss()
                        }
                        is Resource.Error -> {
                            showError(state.message)
                            showLoadingState(false)
                        }
                        Resource.Idle -> {
                            hideError()
                            showLoadingState(false)
                        }
                    }
                }
            }
        }
    }

    private fun showLoadingState(isLoading: Boolean) {
        binding.loadingProgressBar.isVisible = isLoading
        binding.submitButton.isVisible = !isLoading
        binding.cancelButton.isVisible = !isLoading
    }

    private fun showError(message: String) {
        binding.errorTextView.text = message
        binding.errorTextView.isVisible = true
    }

    private fun hideError() {
        binding.errorTextView.isVisible = false
    }





    override fun onStart() {
        super.onStart()
        DialogUtils.setCompactWidth(dialog, resources)
    }

    override fun onDestroy() {
        super.onDestroy()
        _binding=null
    }

}