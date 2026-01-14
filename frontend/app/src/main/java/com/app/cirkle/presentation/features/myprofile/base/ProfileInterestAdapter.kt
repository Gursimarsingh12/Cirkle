package com.app.cirkle.presentation.features.myprofile.base

import android.annotation.SuppressLint
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.databinding.ItemInterestSelectionBinding
import com.app.cirkle.domain.model.user.Interest

class ProfileInterestAdapter(
    private val onInterestToggle: (Interest, Boolean) -> Unit,
    private val onValidationMessage: (String) -> Unit
) : RecyclerView.Adapter<ProfileInterestAdapter.InterestViewHolder>() {

    private var interests: List<Interest> = emptyList()
    private val selectedInterests = mutableSetOf<Int>()

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): InterestViewHolder {
        val binding = ItemInterestSelectionBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return InterestViewHolder(binding)
    }

    override fun onBindViewHolder(holder: InterestViewHolder, position: Int) {
        holder.bind(interests[position])
    }

    override fun getItemCount(): Int = interests.size

    @SuppressLint("NotifyDataSetChanged")
    fun updateInterests(newInterests: List<Interest>) {
        interests = newInterests
        selectedInterests.clear() // Clear previous selections
        notifyDataSetChanged()
    }

    fun setSelectedInterests(selected: List<Interest>) {
        selectedInterests.clear()
        selectedInterests.addAll(selected.map { it.id })
        notifyDataSetChanged()
    }

    fun getSelectedInterests(): List<Interest> {
        return interests.filter { selectedInterests.contains(it.id) }
    }

    fun getSelectedInterestsCount(): Int = selectedInterests.size

    inner class InterestViewHolder(
        private val binding: ItemInterestSelectionBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(interest: Interest) {
            binding.interestName.text = interest.name
            binding.interestCheckbox.isChecked = selectedInterests.contains(interest.id)

            binding.root.setOnClickListener {
                toggleSelection(interest)
            }

            binding.interestCheckbox.setOnCheckedChangeListener { _, isChecked ->
                if (isChecked != selectedInterests.contains(interest.id)) {
                    toggleSelection(interest)
                }
            }
        }

        private fun toggleSelection(interest: Interest) {
            val isSelected = selectedInterests.contains(interest.id)
            if (isSelected) {
                selectedInterests.remove(interest.id)
                onInterestToggle(interest, false)
            } else {
                selectedInterests.add(interest.id)
                onInterestToggle(interest, true)
            }
            binding.interestCheckbox.isChecked = selectedInterests.contains(interest.id)
        }
    }
}