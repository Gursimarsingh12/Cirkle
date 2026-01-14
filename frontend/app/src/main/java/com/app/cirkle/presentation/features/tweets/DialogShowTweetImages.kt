package com.app.cirkle.presentation.features.tweets

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.DialogFragment
import androidx.viewpager2.widget.ViewPager2
import com.app.cirkle.core.utils.common.DialogUtils
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.databinding.DialogImagePreviewBinding
import com.app.cirkle.presentation.adapters.ImagePagerAdapter
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class  DialogShowTweetImages : DialogFragment() {

    private var _binding: DialogImagePreviewBinding? = null
    private val binding get() = _binding!!

    @Inject
    lateinit var imageUtils: ImageUtils

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding =DialogImagePreviewBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val args = requireArguments()
        val imageUrls = args.getStringArrayList("image_urls") ?: emptyList()
        val startPosition = args.getInt("start_position", 0)
        val userName = args.getString("user_name")
        val userId = args.getString("user_id")
        val userIconUrl = args.getString("user_icon_url")
        val likeCount = args.getInt("like_count")

        binding.userName.text = userName
        binding.userId.text = userId
        binding.likeCount.text = likeCount.toString()

        imageUtils.loadImageIntoImageView(userIconUrl?:"",binding.userIcon,circleCrop=true)

        val adapter = ImagePagerAdapter(imageUrls,imageUtils)
        binding.viewPager.adapter = adapter


        binding.viewPager.registerOnPageChangeCallback(object : ViewPager2.OnPageChangeCallback() {
            override fun onPageSelected(position: Int) {
                super.onPageSelected(position)
                if(position==0)
                    binding.left.visibility= View.GONE
                else
                    binding.left.visibility=View.VISIBLE

                if(position==imageUrls.size-1)
                    binding.right.visibility= View.GONE
                else
                    binding.right.visibility=View.VISIBLE
            }
        })

        binding.viewPager.setCurrentItem(startPosition, false)

        binding.left.setOnClickListener {
            binding.viewPager.setCurrentItem(binding.viewPager.currentItem-1,true)
        }

        binding.right.setOnClickListener {
            binding.viewPager.setCurrentItem(binding.viewPager.currentItem+1,true)
        }

        binding.closebtn.setOnClickListener {
            dismiss()
        }
    }


    override fun onStart() {
        super.onStart()
        DialogUtils.setCompactWidth(dialog, resources)
    }



    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
