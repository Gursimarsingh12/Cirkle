package com.app.cirkle.presentation.features.settings

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentProfileSettingsBinding
import com.app.cirkle.databinding.ProfileSettingsItemBinding
import com.app.cirkle.data.local.SecuredSharedPreferences
import androidx.navigation.fragment.findNavController
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.core.utils.common.NavUtils

@AndroidEntryPoint
class ApplicationSettingFragment : BaseFragment<FragmentProfileSettingsBinding>() {

    @Inject
    lateinit var securedPrefs: SecuredSharedPreferences

    override fun getViewBinding(inflater: LayoutInflater, container: ViewGroup?) =
        FragmentProfileSettingsBinding.inflate(inflater, container, false)

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.root.handleVerticalInsets()

        setupItem(binding.myProfileItem, R.drawable.usericon, "My Profile")
        setupItem(binding.resetPasswordItem, R.drawable.padlock, "Reset Password")

        binding.backButton.setOnClickListener { requireActivity().onBackPressedDispatcher.onBackPressed() }

        binding.titleText.text = "Settings"

        binding.myProfileItem.root.setOnClickListener {
            NavUtils.navigateWithSlideAnim(findNavController(), R.id.fragment_my_profile)
        }

        binding.resetPasswordItem.root.setOnClickListener {
            val args = android.os.Bundle().apply { putBoolean("showBackToLoginButton", false) }
            NavUtils.navigateWithSlideAnim(findNavController(), R.id.forgotPasswordFragment, args)
        }

        binding.logoutButton.setOnClickListener {
            securedPrefs.clear()
            val navOptions = androidx.navigation.NavOptions.Builder()
                .setPopUpTo(R.id.app_navigation, true)
                .build()
            findNavController().navigate(R.id.fragment_login, null, navOptions)
        }
    }

    private fun setupItem(itemView: ProfileSettingsItemBinding, iconRes: Int, title: String) {
        val icon = itemView.iconImage
        val text = itemView.titleText
        icon.setImageResource(iconRes)
        text.text = title
    }
}