package com.app.cirkle.presentation.features.onboarding.interests

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
import androidx.recyclerview.widget.GridLayoutManager
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentChooseInterestBinding
import com.app.cirkle.data.model.auth.response.InterestResponse
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.features.onboarding.interests.InterestsViewModel
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyVerticalInsets
import com.app.cirkle.core.utils.common.NavUtils
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class ChooseInterestFragment : BaseFragment<FragmentChooseInterestBinding>() {


    private val adapter: InterestsAdapter by lazy{ InterestsAdapter(){message->
        Toast.makeText(requireContext(),message, Toast.LENGTH_LONG).show()
    } }

    private val viewModel: InterestsViewModel by viewModels()
    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentChooseInterestBinding {
        return FragmentChooseInterestBinding.inflate(inflater)
    }


    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        // Apply insets to the root view for both status bar and navigation bar
        binding.root.applyVerticalInsets()
        
        viewModel.getAllInterest()
        binding.btnConfirmInterests.setOnClickListener {
            val list=adapter.selectedInterests.toList()
            if(list.size<3){
                Toast.makeText(requireContext(),"Please select up to 3 interests!", Toast.LENGTH_LONG).show()
            }else{
                viewModel.addMultipleInterests(list)
            }
        }

        setUpRecycleView()
        setUpObservers()


    }

    private fun setUpObservers(){
        lifecycleScope.launch {
            viewLifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED){
                viewModel.interestsUiState.collect {state->
                    when(state){
                        is InterestsUiState.Error -> {
                            hideLoading()
                            Toast.makeText(requireContext(),state.message, Toast.LENGTH_LONG).show()
                        }
                        InterestsUiState.Idle ->{
                            hideLoading()
                        }
                        InterestsUiState.Loading -> {
                            showLoading()
                        }
                        is InterestsUiState.Success -> {
                            hideLoading()
                            adapter.updateData(state.interests)
                        }
                        InterestsUiState.UpdateComplete -> {
                            hideLoading()
                            NavUtils.navigateWithSlideAnim(findNavController(), R.id.action_fragment_choose_interests_to_fragment_follow_voices)
                        }
                    }
                }
            }
        }
    }

    private fun setUpRecycleView(){
        binding.recyclerView.layoutManager= GridLayoutManager(requireContext(),2)
        binding.recyclerView.adapter=adapter
    }

    private fun getDummyData(): List<InterestResponse> {
        val names = listOf(
            "News", "Gaming", "BlockChain", "AI/ML", "Sports", "Entertainment",
            "Music", "Tech", "Crypto", "Politics", "Computer", "Running",
            "Space", "Finance", "Education"
        ).shuffled()

        return names.mapIndexed { index, name ->
            InterestResponse(id = index + 1, name = name)
        }
    }




}