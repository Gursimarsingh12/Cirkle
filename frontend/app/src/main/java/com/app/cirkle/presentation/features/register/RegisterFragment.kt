package com.app.cirkle.presentation.features.register

import android.os.Bundle
import android.text.Editable
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.google.android.material.datepicker.MaterialDatePicker
import com.app.cirkle.R
import com.app.cirkle.data.model.auth.response.CommandResponse
import com.app.cirkle.databinding.FragmentRegisterBinding
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.common.Resource
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyVerticalInsets
import com.app.cirkle.core.utils.common.NavUtils
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@AndroidEntryPoint
class RegisterFragment : BaseFragment<FragmentRegisterBinding>() {

    private val datePicker = MaterialDatePicker.Builder.datePicker()
        .setTitleText("Select DoB")
        .build()

    private val viewModel: RegisterViewModel by viewModels()

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentRegisterBinding {
        return FragmentRegisterBinding.inflate(inflater, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        // Apply insets to the root view for both status bar and navigation bar
        binding.root.applyVerticalInsets()

        setupInitialData()
        setupClickListeners()
        observeViewModel()
    }

    private fun setupInitialData() {
        viewModel.fetchCommands()
    }

    private fun setupClickListeners() {
        binding.btnRegister.setOnClickListener {
            viewModel.registerUser(
                binding.userId.text.toString(),
                binding.userName.text.toString(),
                binding.password.text.toString()
            )
        }

        binding.selectDob.setOnClickListener {
            datePicker.show(parentFragmentManager, "DATE_PICKER")
        }

        datePicker.addOnPositiveButtonClickListener { selection ->
            val formatter = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
            val formattedDate = formatter.format(Date(selection))
            binding.selectDob.text = formattedDate
            viewModel.selectedDate.value = formattedDate
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.commands.collect { commandList ->
                        if (commandList.isNotEmpty()) {
                            setUpCommandSpinner(commandList)
                        }
                    }
                }

                launch {
                    viewModel.registerViewState.collect { state ->
                        when (state) {
                            is Resource.Error -> {
                                hideLoading()
                                Toast.makeText(requireContext(), state.message, Toast.LENGTH_LONG).show()
                                viewModel.setStateIdle()
                            }
                            Resource.Idle -> {
                                hideLoading()
                            }
                            Resource.Loading -> {
                                showLoading()
                            }
                            is Resource.Success -> {
                                hideLoading()
                                NavUtils.navigateWithSlideAnim(findNavController(), R.id.action_fragment_register_to_fragment_choose_interest)
                            }
                        }
                    }
                }
            }
        }
    }

    private fun setUpCommandSpinner(commandList: List<CommandResponse>) {
        val commandNames = commandList.map { it.name }

        val adapter = ArrayAdapter(
            requireContext(),
            R.layout.drop_down_item,
            commandNames
        )

        binding.selectCommand.setAdapter(adapter)

        binding.selectCommand.setOnItemClickListener { _, _, position, _ ->
            val selectedCommand = commandList[position]
            viewModel.selectedCommand.value = selectedCommand
        }
    }
}