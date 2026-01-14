package com.app.cirkle.presentation.features.forgot_password

import android.app.DatePickerDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.app.cirkle.databinding.FragmentForgotPasswordBinding
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyVerticalInsets
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyBottomInset
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

@AndroidEntryPoint
class ForgotPasswordFragment : BaseFragment<FragmentForgotPasswordBinding>() {

    private val viewModel: ForgotPasswordViewModel by viewModels()

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentForgotPasswordBinding {
        return FragmentForgotPasswordBinding.inflate(inflater, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.root.applyVerticalInsets()
        binding.btnBackToLogin.applyBottomInset()
        
        val showBackToLoginButton = arguments?.getBoolean("showBackToLoginButton", true) ?: true
        binding.btnBackToLogin.visibility = if (showBackToLoginButton) View.VISIBLE else View.GONE
        
        setupClickListeners()
        observeViewModel()
    }

    private fun setupClickListeners() {
        binding.etDob.setOnClickListener {
            showDatePickerDialog()
        }

        binding.btnResetPassword.setOnClickListener {
            val userId = binding.etUserId.text.toString().trim()
            val dob = binding.etDob.text.toString().trim()
            val newPassword = binding.etNewPassword.text.toString().trim()
            viewModel.resetPassword(userId, dob, newPassword)
        }

        binding.btnBackToLogin.setOnClickListener {
            findNavController().popBackStack()
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    when (state) {
                        is ForgotPasswordUiState.Idle -> hideLoading()
                        is ForgotPasswordUiState.Loading -> showLoading()
                        is ForgotPasswordUiState.Success -> {
                            hideLoading()
                            Toast.makeText(requireContext(), state.message, Toast.LENGTH_LONG).show()
                            findNavController().popBackStack()
                        }
                        is ForgotPasswordUiState.Error -> {
                            hideLoading()
                            Toast.makeText(requireContext(), state.message, Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        }
    }

    private fun showDatePickerDialog() {
        val calendar = Calendar.getInstance()
        val datePickerDialog = DatePickerDialog(
            requireContext(),
            { _, year, month, dayOfMonth ->
                val selectedDate = Calendar.getInstance()
                selectedDate.set(year, month, dayOfMonth)
                val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
                binding.etDob.setText(dateFormat.format(selectedDate.time))
            },
            calendar.get(Calendar.YEAR),
            calendar.get(Calendar.MONTH),
            calendar.get(Calendar.DAY_OF_MONTH)
        )
        datePickerDialog.show()
    }
} 