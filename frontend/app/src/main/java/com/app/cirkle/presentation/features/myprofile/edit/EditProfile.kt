package com.app.cirkle.presentation.features.myprofile.edit

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.addCallback
import androidx.core.widget.addTextChangedListener
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.fragment.app.setFragmentResultListener
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.bumptech.glide.Glide
import com.google.android.material.chip.Chip
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.core.utils.common.NavUtils
import com.app.cirkle.databinding.FragmentEditProfileBinding
import com.app.cirkle.domain.model.user.Interest
import com.app.cirkle.domain.model.user.MyProfile
import com.app.cirkle.presentation.features.myprofile.edit.InterestSelectionDialogFragment
import com.app.cirkle.AppNavigationDirections
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@AndroidEntryPoint
class EditProfile : Fragment() {

    private var _binding: FragmentEditProfileBinding? = null
    private val binding get() = _binding!!
    private val viewModel: EditProfileViewModel by viewModels()
    private val imageViewModel: EditProfileImageViewModel by activityViewModels()

    @Inject
    lateinit var imageUtils: ImageUtils

    private var allInterests: List<Interest> = emptyList()
    private var selectedInterests: List<Interest> = emptyList()



    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requireActivity().onBackPressedDispatcher.addCallback(this) {
            imageViewModel.clear()
            findNavController().popBackStack()
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentEditProfileBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupClickListeners()
        setupTextWatchers()
        observeViewModel()
        setUpResultListener()
    }

    private fun setupClickListeners() {
        binding.backButton.setOnClickListener {
            findNavController().navigateUp()
        }

        binding.changeProfile.setOnClickListener {
            val action= EditProfileDirections.actionFragmentEditProfileToFragmentCamera(true,true)
            NavUtils.navigateWithSlideAnimAndPopUpTo(findNavController(), action.actionId, R.id.fragment_edit_profile, false, action.arguments)
        }

        binding.profileImageView.setOnClickListener {
            val action= EditProfileDirections.actionFragmentEditProfileToFragmentCamera(true,true)
            NavUtils.navigateWithSlideAnimAndPopUpTo(findNavController(), action.actionId, R.id.fragment_edit_profile, false, action.arguments)
        }

        binding.coverImageView.setOnClickListener {
            val action= EditProfileDirections.actionFragmentEditProfileToFragmentCamera(false,true)
            NavUtils.navigateWithSlideAnimAndPopUpTo(findNavController(), action.actionId, R.id.fragment_edit_profile, false, action.arguments)
        }

        binding.changeBanner.setOnClickListener {
            val action= EditProfileDirections.actionFragmentEditProfileToFragmentCamera(false,true)
            NavUtils.navigateWithSlideAnimAndPopUpTo(findNavController(), action.actionId, R.id.fragment_edit_profile, false, action.arguments)
        }

        binding.saveProfileChanges.setOnClickListener {
            if (validateInterests()) {
                viewModel.saveProfile(imageViewModel.profileImage.value,imageViewModel.bannerImage.value)
            }
        }

        binding.manageInterestsButton.setOnClickListener {
            showInterestSelectionDialog()
        }

    }

    private fun setUpResultListener(){
        setFragmentResultListener("camera_result") { _, bundle ->
            val filePath = bundle.getString("image_file_path")
            val isProfile=bundle.getBoolean("is_profile",false)
            val file = filePath?.let { File(it) }
            if(file!=null) {
                if(isProfile) {
                    imageViewModel.addProfileImage(file)
                }else{
                    imageViewModel.addBannerImage(file)
                }
            }else
                Toast.makeText(requireContext(),"Unable to click image. Try Again!", Toast.LENGTH_SHORT).show()

        }
    }

    private fun setupTextWatchers() {
        binding.etDisplayName.addTextChangedListener { text ->
            viewModel.updateName(text.toString())
            imageViewModel.updatedName=text.toString()
        }

        binding.etBio.addTextChangedListener { text ->
            viewModel.updateBio(text.toString())
            imageViewModel.bio=text.toString()
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.uiState.collect { state ->
                        handleUiState(state)
                    }
                }

                launch {
                    viewModel.currentName.collect { name ->
                        if (binding.etDisplayName.text.toString() != name) {
                            binding.etDisplayName.setText(name)
                        }
                    }
                }

                launch {
                    viewModel.currentBio.collect { bio ->
                        if (binding.etBio.text.toString() != bio) {
                            binding.etBio.setText(bio)
                        }
                    }
                }

                launch {
                    viewModel.selectedInterests.collect { interests ->
                        selectedInterests = interests
                        updateInterestChips()
                    }
                }

                launch {
                    imageViewModel.bannerImage.collect { image->
                        if(image!=null){
                            Glide.with(binding.coverImageView.context)
                                .load(image)
                                .into(binding.coverImageView)
                            binding.etBio.setText(imageViewModel.bio)
                            binding.etDisplayName.setText(imageViewModel.updatedName)
                        }
                    }
                }

                launch {
                    imageViewModel.profileImage.collect { image->
                        if(image!=null){
                            Glide.with(binding.profileImageView.context)
                                .load(image)
                                .circleCrop()
                                .into(binding.profileImageView)
                            binding.etBio.setText(imageViewModel.bio)
                            binding.etDisplayName.setText(imageViewModel.updatedName)
                        }
                    }
                }
            }
        }
    }

    private fun handleUiState(state: EditProfileUiState) {
        when (state.profileState) {
            is EditProfileState.Loading -> {
                // Show loading for profile
            }
            is EditProfileState.Success -> {
                setupProfileData(state.profileState.myProfile)
            }
            is EditProfileState.Error -> {
                Toast.makeText(requireContext(), state.profileState.message, Toast.LENGTH_SHORT).show()
            }
        }

        when (state.allInterestsState) {
            is AllInterestsState.Loading -> {
                // Loading interests
            }
            is AllInterestsState.Success -> {
                allInterests = state.allInterestsState.interests
                // If we have profile data already loaded, reprocess interests
                if (state.profileState is EditProfileState.Success) {
                    setupProfileData(state.profileState.myProfile)
                }
            }
            is AllInterestsState.Error -> {
                Toast.makeText(requireContext(), state.allInterestsState.message, Toast.LENGTH_SHORT).show()
            }
        }

        when (state.saveState) {
            is SaveState.Idle -> {
                binding.saveProfileChanges.isEnabled = true
                binding.saveProfileChanges.text = "Save Changes"
            }
            is SaveState.Saving -> {
                binding.saveProfileChanges.isEnabled = false
                binding.saveProfileChanges.text = "Saving..."
            }
            is SaveState.Success -> {
                Toast.makeText(requireContext(), "Profile saved successfully!", Toast.LENGTH_SHORT).show()
                val action = AppNavigationDirections.actionToFragmentMyProfile()
                NavUtils.navigateWithSlideAnimAndPopUpTo(findNavController(), action.actionId, R.id.fragment_edit_profile, true, action.arguments)
                viewModel.clearSaveState()

            }
            is SaveState.Error -> {
                Toast.makeText(requireContext(), state.saveState.message, Toast.LENGTH_SHORT).show()
                viewModel.clearSaveState()
            }
        }
    }

    private fun setupProfileData(myProfile: MyProfile) {
        // Set user data
        binding.etDisplayName.setText(myProfile.name)
        binding.etBio.setText(myProfile.bio)

        if(imageViewModel.profileImage.value==null) {
            imageUtils.loadImageIntoImageView(
                myProfile.profileUrl,
                binding.profileImageView,
                circleCrop = true
            )
        }
        if(imageViewModel.bannerImage.value==null) {
            imageUtils.loadImageIntoImageView(
                myProfile.bannerUrl,
                binding.coverImageView
            )
        }

        // Find matching interests from all interests and set them as selected
        if (allInterests.isNotEmpty() && myProfile.interests.isNotEmpty()) {
            val userInterestsDomain = myProfile.interests.mapNotNull { interestName ->
                val found = allInterests.find { it.name.equals(interestName, ignoreCase = true) }
                android.util.Log.d("EditProfile", "Matching '$interestName' -> ${found?.let { "${it.id}:${it.name}" } ?: "NOT FOUND"}")
                found
            }

            android.util.Log.d("EditProfile", "Matched interests: ${userInterestsDomain.map { "${it.id}:${it.name}" }}")
            selectedInterests = userInterestsDomain
            viewModel.setSelectedInterests(selectedInterests)
        }
    }

    private fun validateInterests(): Boolean {
        val count = selectedInterests.size
        return when {
            count < 3 -> {
                Toast.makeText(requireContext(), "Please select at least 3 interests", Toast.LENGTH_SHORT).show()
                false
            }
            count > 8 -> {
                Toast.makeText(requireContext(), "Please select maximum 8 interests", Toast.LENGTH_SHORT).show()
                false
            }
            else -> true
        }
    }

    private fun showInterestSelectionDialog() {
        if (allInterests.isNotEmpty()) {
            // Filter out already selected interests
            val availableInterests = allInterests.filter { interest ->
                selectedInterests.none { selected -> selected.id == interest.id }
            }

            if (availableInterests.isEmpty()) {
                Toast.makeText(requireContext(), "All interests are already selected", Toast.LENGTH_SHORT).show()
                return
            }

            val dialog = InterestSelectionDialogFragment.newInstance(
                availableInterests = availableInterests,
                currentlySelected = emptyList() // Don't show current selection in dialog
            ) { newSelectedInterests ->
                // Add newly selected interests to existing ones
                val updatedInterests = selectedInterests.toMutableList()
                newSelectedInterests.forEach { newInterest ->
                    if (updatedInterests.none { it.id == newInterest.id }) {
                        updatedInterests.add(newInterest)
                    }
                }
                selectedInterests = updatedInterests
                viewModel.setSelectedInterests(selectedInterests)
                updateManageButtonState()
            }
            dialog.show(parentFragmentManager, "InterestSelectionDialog")
        } else {
            Toast.makeText(requireContext(), "Loading interests...", Toast.LENGTH_SHORT).show()
        }
    }

    private fun updateManageButtonState() {
        val canAddMore = selectedInterests.size < 8
        binding.manageInterestsButton.isEnabled = canAddMore
        binding.manageInterestsButton.alpha = if (canAddMore) 1.0f else 0.5f

        if (!canAddMore) {
            binding.manageInterestsButton.text = "Max Interests (8/8)"
        } else {
            binding.manageInterestsButton.text = "Manage Interests"
        }
    }

    private fun updateInterestChips() {
        binding.interestChipGroup.removeAllViews()

        selectedInterests.forEach { interest ->
            val chip = Chip(requireContext()).apply {
                text = interest.name
                setChipBackgroundColorResource(R.color.primc)
                setTextColor(resources.getColor(R.color.white, null))
                isCloseIconVisible = true
                setOnCloseIconClickListener {
                    val updatedList = selectedInterests.toMutableList()
                    updatedList.remove(interest)
                    selectedInterests = updatedList
                    viewModel.setSelectedInterests(selectedInterests)
                    updateManageButtonState()
                }
            }
            binding.interestChipGroup.addView(chip)
        }

        updateManageButtonState()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}