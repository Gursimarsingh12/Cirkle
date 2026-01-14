package com.app.cirkle.presentation.features.onboarding.info

import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentOnBoardingBinding
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyVerticalInsets
import com.app.cirkle.core.utils.common.NavUtils
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class OnBoardingFragment : BaseFragment<FragmentOnBoardingBinding>() {

    private val viewModel: OnBoardingViewModel by viewModels()

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentOnBoardingBinding {
        return FragmentOnBoardingBinding.inflate(inflater)
    }
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.root.applyVerticalInsets()
        lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                val loggedIn = viewModel.isLoggedIn()
                if (loggedIn) {
                    NavUtils.navigateWithSlideAnimAndPopUpTo(findNavController(), R.id.action_fragment_onboarding_to_fragment_home, R.id.fragment_onboarding, true)
                }
            }
        }

        binding.btnStart.setOnClickListener {
            Log.d("NavCont","ButtonFunc")
            NavUtils.navigateWithSlideAnim(findNavController(), R.id.action_fragment_onboarding_to_fragment_login)
        }
    }
}