package com.app.cirkle.presentation.features.myprofile.edit

import android.app.Dialog
import android.os.Bundle
import android.widget.Toast
import androidx.fragment.app.DialogFragment
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.app.cirkle.databinding.DialogInterestSelectionBinding
import com.app.cirkle.domain.model.user.Interest
import com.app.cirkle.presentation.features.myprofile.base.ProfileInterestAdapter
import android.view.ViewGroup
import android.view.View
import com.app.cirkle.core.utils.common.DialogUtils

class InterestSelectionDialogFragment : DialogFragment() {

    private var _binding: DialogInterestSelectionBinding? = null
    private val binding get() = _binding!!

    private lateinit var interestsAdapter: ProfileInterestAdapter
    private var onInterestsSelected: ((List<Interest>) -> Unit)? = null
    private var availableInterests: List<Interest> = emptyList()
    private var currentlySelectedInterests: List<Interest> = emptyList()

    companion object {
        fun newInstance(
            availableInterests: List<Interest>,
            currentlySelected: List<Interest>,
            onInterestsSelected: (List<Interest>) -> Unit
        ): InterestSelectionDialogFragment {
            return InterestSelectionDialogFragment().apply {
                this.availableInterests = availableInterests
                this.currentlySelectedInterests = currentlySelected
                this.onInterestsSelected = onInterestsSelected
            }
        }
    }

    override fun onCreateDialog(savedInstanceState: Bundle?): Dialog {
        _binding = DialogInterestSelectionBinding.inflate(layoutInflater)

        setupRecyclerView()

        return MaterialAlertDialogBuilder(requireContext())
            .setTitle("Manage Your Interests")
            .setView(binding.root)
            .setPositiveButton("Add Selected") { _, _ ->
                val selectedInterests = interestsAdapter.getSelectedInterests()
                if (selectedInterests.isNotEmpty()) {
                    onInterestsSelected?.invoke(selectedInterests)
                    dismiss()
                } else {
                    Toast.makeText(requireContext(), "Please select at least one interest to add", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Cancel") { _, _ ->
                dismiss()
            }
            .create()
    }

    override fun onStart() {
        super.onStart()
        DialogUtils.setCompactWidth(dialog, resources)
    }

    private fun setupRecyclerView() {
        interestsAdapter = ProfileInterestAdapter(
            onInterestToggle = { interest, isSelected ->
                // Handle individual interest selection if needed
            },
            onValidationMessage = { message ->
                Toast.makeText(requireContext(), message, Toast.LENGTH_SHORT).show()
            }
        )

        binding.interestsRecyclerView.apply {
            adapter = interestsAdapter
            layoutManager = LinearLayoutManager(requireContext())
        }

        // Set data
        interestsAdapter.updateInterests(availableInterests)
        interestsAdapter.setSelectedInterests(currentlySelectedInterests)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}