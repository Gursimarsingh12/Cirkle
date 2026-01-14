package com.app.cirkle.core.components

import android.app.AlertDialog
import android.content.Context
import android.view.LayoutInflater
import com.app.cirkle.R

class LoadingDialog(private val context: Context) {
    private var dialog: AlertDialog? = null

    fun show() {
        if (dialog == null) {
            val builder = AlertDialog.Builder(context)
            val view = LayoutInflater.from(context).inflate(R.layout.dialog_loading, null)
            builder.setView(view)
            builder.setCancelable(false) // Prevent dismissing by tapping outside
            dialog = builder.create()
        }
        dialog?.show()
    }

    fun dismiss() {
        dialog?.dismiss()
        dialog = null
    }
}