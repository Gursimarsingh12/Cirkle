package com.app.cirkle.presentation.common

import android.app.AlertDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.viewbinding.ViewBinding
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyBottomInset
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyVerticalInsets
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyAllInsets

abstract class BaseFragment<VB : ViewBinding> : Fragment() {

    private var _binding: VB? = null
    protected val binding get() = _binding!!

    private var loadingDialog: AlertDialog? = null

    abstract fun getViewBinding(inflater: LayoutInflater, container: ViewGroup?): VB

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?,
    ): View? {
        _binding = getViewBinding(inflater, container)
        if (shouldApplyBottomInset()) {
            binding.root.handleBottomInset()
        }
        return binding.root
    }

    open fun showLoading() {
        if (loadingDialog == null) {
            loadingDialog = AlertDialog.Builder(requireContext())
                .setView(LayoutInflater.from(context).inflate(R.layout.dialog_loading, null))
                .setCancelable(false)
                .create()
        }
        loadingDialog?.show()
    }

    open fun hideLoading() {
        loadingDialog?.dismiss()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
        loadingDialog?.dismiss()
        loadingDialog = null
    }


    protected fun View.handleBottomInset() = applyBottomInset()

    protected fun View.handleVerticalInsets() = applyVerticalInsets()

    protected fun View.handleAllInsets() = applyAllInsets()

    protected open fun shouldApplyBottomInset(): Boolean = false
}