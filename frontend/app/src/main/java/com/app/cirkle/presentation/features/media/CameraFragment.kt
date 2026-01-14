package com.app.cirkle.presentation.features.media

import com.app.cirkle.databinding.FragmentCameraBinding
import android.Manifest
import android.annotation.SuppressLint
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Matrix
import android.graphics.Rect
import android.graphics.YuvImage
import android.media.Image
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.navigation.fragment.navArgs
import com.app.cirkle.R
import com.app.cirkle.core.utils.permissions.PermissionManager
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.common.SharedImageViewModel
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import com.app.cirkle.core.utils.common.NavUtils


class CameraFragment : BaseFragment<FragmentCameraBinding>() {


    private val navArgs: CameraFragmentArgs by navArgs()
    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentCameraBinding {
        return FragmentCameraBinding.inflate(inflater)
    }

    private val requestCameraPermissionLauncher =
        registerForActivityResult(
            ActivityResultContracts.RequestPermission()
        ) { isGranted ->
            if (isGranted) {
                startCamera()
            } else {
                Toast.makeText(context, "Camera permission denied", Toast.LENGTH_LONG).show()
                findNavController().navigateUp()
            }
        }

    private val imageViewModel: SharedImageViewModel by activityViewModels()

    private lateinit var camera:Camera
    private lateinit var cameraProvider: ProcessCameraProvider
    private lateinit var preview: Preview
    private lateinit var backgroundExecutor: ExecutorService
    private var lensFacing= CameraSelector.LENS_FACING_BACK

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        backgroundExecutor= Executors.newFixedThreadPool(1)
    }



    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.root.handleAllInsets()
        binding.cameraCard.handleBottomInset()
        if (!PermissionManager.hasCameraPermissions(requireContext())) {
            requestCameraPermissionLauncher.launch(Manifest.permission.CAMERA)
        } else {
            startCamera()
        }
        setOnClickListeners()
    }

    private fun startCamera(){
        val cameraProviderFuture = ProcessCameraProvider.getInstance(requireContext())
        cameraProviderFuture.addListener({
            cameraProvider = cameraProviderFuture.get()

            preview = Preview.Builder()
                .build()
                .also {
                    it.surfaceProvider = binding.cameraPreview.surfaceProvider
                }
            val cameraSelector =
                CameraSelector.Builder().requireLensFacing(lensFacing).build()
            try {
                setUpImageCapture(cameraProvider,cameraSelector,preview)
            } catch(_: Exception) {

            }
        }, ContextCompat.getMainExecutor(requireContext()))
    }

    private lateinit var imageCapture: ImageCapture

    private fun setUpImageCapture(
        cameraProvider: ProcessCameraProvider,
        cameraSelector: CameraSelector,
        preview: Preview
    ){

        imageCapture= ImageCapture.Builder()
            .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
            .setFlashMode(ImageCapture.FLASH_MODE_AUTO)
            .setTargetRotation(requireView().display.rotation)
            .build()
        try{
            camera=cameraProvider.bindToLifecycle(this,cameraSelector,imageCapture,preview/**,imageAnalyzer**/)
        }catch(e: Exception){
            Toast.makeText(requireContext(),e.message, Toast.LENGTH_LONG).show()
            findNavController().navigateUp()
        }finally {

        }

    }

    private fun setOnClickListeners() {
        binding.capture.onCaptureClick = {
            imageCapture.takePicture(backgroundExecutor, object : ImageCapture.OnImageCapturedCallback() {
                @SuppressLint("UnsafeOptInUsageError")
                override fun onCaptureSuccess(image: ImageProxy) {
                    super.onCaptureSuccess(image)
                    hideLoading()
                    val mediaImage = imageProxyToBitmap(image,lensFacing == CameraSelector.LENS_FACING_FRONT)
                    hideLoading()
                    lifecycleScope.launch {
                        imageViewModel.setImage(mediaImage)
                        val isCircle=navArgs.isCircle
                        val action= CameraFragmentDirections.actionFragmentCameraToFragmentClickedImagePreview(isCircle,navArgs.isFromProfile,navArgs.isFromEditTweet)
                        NavUtils.navigateWithSlideAnimAndPopUpTo(findNavController(), action.actionId, R.id.fragment_camera, true, action.arguments)
                    }
                }

                override fun onCaptureStarted() {
                    super.onCaptureStarted()
                    showLoading()
                }
            })
        }
        binding.toggleCamera.setOnClickListener {
            toggleCamera()
        }
        binding.navigateUp.setOnClickListener {
            findNavController().navigateUp()
        }
    }

    private fun toggleCamera(){
        lensFacing = if(lensFacing== CameraSelector.LENS_FACING_BACK){
            CameraSelector.LENS_FACING_FRONT
        }else{
            CameraSelector.LENS_FACING_BACK
        }
        val cameraSelector= CameraSelector.Builder().requireLensFacing(lensFacing).build()
        try{
            cameraProvider.unbindAll()
            camera=cameraProvider.bindToLifecycle(this,cameraSelector,imageCapture,preview/**,imageAnalyzer**/)
        }catch(e: Exception){
            Toast.makeText(requireContext(),e.message, Toast.LENGTH_LONG).show()
            findNavController().navigateUp()
        }
    }

    override fun onPause() {
        super.onPause()
    }

    override fun onStop() {
        super.onStop()
    }

    @SuppressLint("UnsafeOptInUsageError")
    fun imageProxyToBitmap(image: ImageProxy, isFrontCamera: Boolean): Bitmap {
        val buffer = image.planes[0].buffer
        val bytes = ByteArray(buffer.remaining())
        buffer.get(bytes)

        val originalBitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)!!

        val rotationDegrees = image.imageInfo.rotationDegrees

        val matrix = Matrix().apply {
            postRotate(rotationDegrees.toFloat())
            if (isFrontCamera) {
                postScale(-1f, 1f) // Mirror horizontally
                postTranslate(originalBitmap.width.toFloat(), 0f) // Adjust for mirrored position
            }
        }

        val rotatedBitmap = Bitmap.createBitmap(
            originalBitmap,
            0,
            0,
            originalBitmap.width,
            originalBitmap.height,
            matrix,
            true
        )

        image.close()
        return rotatedBitmap
    }


    override fun onDestroy() {
        super.onDestroy()
        try {
            cameraProvider.unbindAll()
        }catch (e: Exception){

        }
    }





}