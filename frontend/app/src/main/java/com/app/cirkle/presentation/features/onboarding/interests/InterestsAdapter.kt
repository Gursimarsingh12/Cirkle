package com.app.cirkle.presentation.features.onboarding.interests

import android.annotation.SuppressLint
import android.util.Log
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.domain.model.user.Interest
import com.app.cirkle.core.components.SelectableChipView

class InterestsAdapter(val showMessage:(String)->Unit): RecyclerView.Adapter<InterestsAdapter.InterestViewHolder>() {

    private var interests:List<Interest> =emptyList()
    val selectedInterests=mutableSetOf<Int>()
    override fun onCreateViewHolder(
        parent: ViewGroup,
        viewType: Int
    ): InterestViewHolder {
        return InterestViewHolder(SelectableChipView(parent.context))
    }

    override fun onBindViewHolder(
        holder: InterestViewHolder,
        position: Int
    ) {
       holder.bind(interests[position],position)
    }

    override fun getItemCount(): Int {
        return interests.size
    }

    @SuppressLint("NotifyDataSetChanged")
    fun updateData(list:List<Interest>){
        interests=list
        notifyDataSetChanged()
    }


    inner class InterestViewHolder(val view: SelectableChipView): RecyclerView.ViewHolder(view){
        fun bind(interest: Interest, position: Int){
            view.setText(interest.name)
            view.setSelectedState(interest.checked)
            view.setOnSelectedStateChangeListener { state->
                if(!state){
                    if(selectedInterests.size<8) {
                        selectedInterests.add(interest.id)
                        Log.d("BackEnd","size: ${selectedInterests.size}data: $selectedInterests")
                        interests[position].checked=true
                        notifyItemChanged(position)
                    }
                    else{
                        showMessage("Maximum 8 interests allowed!")
                    }
                }else{
                    selectedInterests.remove(interest.id)
                    Log.d("BackEnd","size: ${selectedInterests.size}data: $selectedInterests")
                    interests[position].checked=false
                    notifyItemChanged(position)
                }
            }
        }
    }
}