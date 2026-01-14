package com.app.cirkle.presentation.features.login

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
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentLoginBinding
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.common.Resource
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyVerticalInsets
import com.app.cirkle.core.utils.common.NavUtils
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class LoginFragment : BaseFragment<FragmentLoginBinding>() {

    private val viewModel: LoginViewModel by viewModels()

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentLoginBinding {
        return FragmentLoginBinding.inflate(inflater, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        // Apply insets to the root view for both status bar and navigation bar
        binding.root.applyVerticalInsets()

        setupClickListeners()
        observeViewModel()
    }

    private fun setupClickListeners() {
        binding.btnLogin.setOnClickListener {
            val userId = binding.etUserId.text.toString()
            val password = binding.etPassword.text.toString()
            viewModel.login(userId, password)
        }

        binding.btnToRegister.setOnClickListener {
            NavUtils.navigateWithSlideAnim(findNavController(), R.id.action_fragment_login_to_fragment_register)
        }

        binding.forgotPassword.setOnClickListener {
            NavUtils.navigateWithSlideAnim(findNavController(), R.id.action_fragment_login_to_forgot_password_fragment)
        }
    }

    private fun observeViewModel() {
        lifecycleScope.launch {
            viewLifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.viewState.collect { state ->
                    when (state) {
                        is Resource.Idle -> hideLoading()
                        is Resource.Loading -> showLoading()
                        is Resource.Success -> {
                            hideLoading()
                            navigateToHome()
                        }
                        is Resource.Error -> {
                            hideLoading()
                            Toast.makeText(requireContext(), state.message, Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        }
    }

    private fun navigateToHome() {
        val navController = findNavController()
        val currentDestination = navController.currentDestination?.id
        if (currentDestination == R.id.fragment_login) {
            NavUtils.navigateWithSlideAnimAndPopUpTo(navController, R.id.action_fragment_login_to_fragment_home, R.id.fragment_onboarding, true)
        }
    }
}
