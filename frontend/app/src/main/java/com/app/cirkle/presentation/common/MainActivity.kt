package com.app.cirkle.presentation.common

import android.graphics.Color
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.content.ContextCompat
import androidx.core.graphics.drawable.toDrawable
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.isVisible
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.NavController
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.NavigationUI
import androidx.navigation.ui.setupActionBarWithNavController
import androidx.navigation.ui.setupWithNavController
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.NavUtils
import com.app.cirkle.core.utils.extensions.SessionManager
import com.app.cirkle.databinding.ActivityMainBinding
import com.app.cirkle.presentation.features.onboarding.info.OnBoardingViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking


@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    private lateinit var navHostFragment: NavHostFragment
    private lateinit var navController: NavController

    private var _binding: ActivityMainBinding? = null
    private val binding get() = _binding!!

    private val cacheViewModel: MainSharedCachingViewModel by viewModels()
    private val viewModel: OnBoardingViewModel by viewModels()

    private var menuRef: Menu? = null
    private var lastNavTime = 0L
    private val debounceTime = 200L
    private var lastItemId = -1

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        enableEdgeToEdge()

        val isLoggedIn = runBlocking { viewModel.isLoggedIn() }
        initUI(isLoggedIn)
    }

    private fun initUI(isLoggedIn: Boolean) {
        _binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        ViewCompat.setOnApplyWindowInsetsListener(binding.root) { v, windowInsets ->
            val systemBars = windowInsets.getInsets(WindowInsetsCompat.Type.systemBars())
            binding.navHostFragment.setPadding(
                systemBars.left,
                0,
                systemBars.right,
                0
            )
            binding.appbar.setPadding(0, systemBars.top, 0, 0)
            binding.bottomNavigation.setPadding(
                systemBars.left,
                0,
                systemBars.right,
                systemBars.bottom
            )
            
            windowInsets
        }

        setSupportActionBar(binding.toolbar)

        navHostFragment = supportFragmentManager.findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        navController = navHostFragment.navController

        val navGraph = navController.navInflater.inflate(R.navigation.app_navigation)
        navGraph.setStartDestination(if (isLoggedIn) R.id.fragment_home else R.id.fragment_onboarding)
        navController.graph = navGraph

        configureNavigationUI()
        setUpClickListeners()
        setUpUiState()
    }

    private fun configureNavigationUI() {
        navController.addOnDestinationChangedListener { _, destination, _ ->
            binding.root.background = Color.WHITE.toDrawable()
            when (destination.id) {
                R.id.fragment_onboarding,
                R.id.fragment_login,
                R.id.fragment_choose_interests,
                R.id.fragment_follow_voices,
                R.id.fragment_camera -> {
                    binding.appbar.visibility = View.GONE
                    binding.bottomNavigation.visibility = View.GONE
                }

                R.id.fragment_home,
                R.id.fragment_create -> {
                    supportActionBar?.title = ""
                    binding.toolbar.title = ""
                    cacheViewModel.hasFollowRequests()
                    binding.appbar.visibility = View.VISIBLE
                    binding.bottomNavigation.visibility = View.VISIBLE
                }

                R.id.fragment_activity -> {
                    binding.root.background = Color.WHITE.toDrawable()
                    binding.appbar.visibility = View.VISIBLE
                    binding.bottomNavigation.visibility = View.VISIBLE
                }

                R.id.fragment_explore,
                R.id.fragment_my_profile -> {
                    binding.appbar.visibility = View.GONE
                    binding.bottomNavigation.visibility = View.VISIBLE
                }

                R.id.fragment_edit_profile,
                R.id.fragment_setting -> {
                    binding.bottomNavigation.visibility = View.GONE
                }

                R.id.fragment_notification,
                R.id.fragment_messages -> {
                    binding.root.background = ContextCompat.getColor(this, R.color.primc_light).toDrawable()
                    binding.bottomNavigation.visibility = View.GONE
                    binding.appbar.visibility = View.GONE
                }

                R.id.fragment_post,
                R.id.fragment_user_profile -> {
                    binding.bottomNavigation.visibility = View.GONE
                    binding.appbar.visibility = View.VISIBLE
                }

                R.id.fragment_comment_replies -> {
                    binding.appbar.isVisible = true
                    binding.bottomNavigation.isVisible = false
                }
                R.id.shareBottomSheetFragment -> {
                    binding.appbar.isVisible = true
                }
            }
        }

        val appBarConfiguration = AppBarConfiguration(
            setOf(
                R.id.fragment_home,
                R.id.fragment_explore,
                R.id.fragment_create,
                R.id.fragment_activity,
                R.id.fragment_my_profile
            )
        )

        setupActionBarWithNavController(navController, appBarConfiguration)
        binding.bottomNavigation.setupWithNavController(navController)
    }

    private fun navigateWithSingleTop(tabId: Int): Boolean {
        val navOptions = androidx.navigation.NavOptions.Builder()
            .setLaunchSingleTop(true)
            .setPopUpTo(tabId, false)
            .build()
        navController.navigate(tabId, null, navOptions)
        return true
    }

    private fun setUpClickListeners() {
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            val currentTime = System.currentTimeMillis()
            if (item.itemId == lastItemId && currentTime - lastNavTime < debounceTime) {
                return@setOnItemSelectedListener false
            }
            lastNavTime = currentTime
            lastItemId = item.itemId

            return@setOnItemSelectedListener when (item.itemId) {
                R.id.fragment_my_profile -> navigateWithSingleTop(R.id.fragment_my_profile)
                R.id.fragment_home -> navigateWithSingleTop(R.id.fragment_home)
                R.id.fragment_activity -> navigateWithSingleTop(R.id.fragment_activity)
                else -> {
                    NavigationUI.onNavDestinationSelected(item, navController)
                    true
                }
            }
        }

        binding.bottomNavigation.setOnItemReselectedListener { item ->
            if (item.itemId == R.id.fragment_my_profile) {
                val navHostFragment = supportFragmentManager.findFragmentById(R.id.nav_host_fragment)
                val fragment = navHostFragment?.childFragmentManager?.fragments?.firstOrNull()
                if (fragment is com.app.cirkle.presentation.features.myprofile.base.MyProfileFragment) {
                    fragment.scrollToTopOrRefresh()
                }
            }
        }
    }

    private fun setUpUiState() {
        lifecycleScope.launch {
            cacheViewModel.hasFollowRequestState.collect {
                updateNotificationIcon(it)
            }
        }
        lifecycleScope.launch {
            lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                SessionManager.logoutFlow.collect {
                    cacheViewModel.logout()
                    Toast.makeText(baseContext, "Session expired please login again!", Toast.LENGTH_LONG).show()
                    finish()
                }
            }
        }
    }

    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.top_bar_menu, menu)
        menuRef = menu
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.menu_item_chats -> {
                NavUtils.navigateWithSlideAnim(navController, R.id.action_to_messages)
                true
            }

            R.id.menu_item_notifications -> {
                NavUtils.navigateWithSlideAnim(navController, R.id.action_to_notifications)
                true
            }

            else -> false
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        return navController.navigateUp() || super.onSupportNavigateUp()
    }

    fun updateChatNotificationIcon(isUnread: Boolean) {
        val iconRes = if (isUnread) R.drawable.messages_unread else R.drawable.messages
        menuRef?.findItem(R.id.menu_item_chats)?.setIcon(iconRes)
    }

    fun updateNotificationIcon(isUnread: Boolean) {
        val iconRes = if (isUnread) R.drawable.notification_unread else R.drawable.notifications
        menuRef?.findItem(R.id.menu_item_notifications)?.setIcon(iconRes)
    }

    override fun onDestroy() {
        super.onDestroy()
        _binding = null
    }
}