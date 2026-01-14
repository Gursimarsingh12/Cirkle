package com.app.cirkle.presentation.features.register

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.data.model.auth.request.RegisterRequest
import com.app.cirkle.data.model.auth.response.CommandResponse
import com.app.cirkle.domain.repository.AuthRepository
import com.app.cirkle.presentation.features.login.LoginViewState
import com.app.cirkle.core.utils.validation.AuthInputValidator
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.presentation.common.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class RegisterViewModel @Inject constructor(private val repository: AuthRepository): ViewModel() {

    private val _registerViewState=MutableStateFlow<Resource<Unit>>(Resource.Idle)
    val registerViewState: StateFlow<Resource<Unit>> =_registerViewState

    private val _commands = MutableStateFlow<List<CommandResponse>>(emptyList())
    val commands: StateFlow<List<CommandResponse>> = _commands

    val selectedCommand= MutableStateFlow<CommandResponse>(CommandResponse(-1,"null"))
    val selectedDate= MutableStateFlow<String>("null")

    fun registerUser(id: String, name: String, password: String) {
        val date = selectedDate.value
        val commandId = selectedCommand.value.id

        if (date == "null" || commandId == -1) {
            _registerViewState.value = Resource.Error("Date or Command not selected")
            return
        }

        if (!AuthInputValidator.isValidUserId(id)) {
            _registerViewState.value = Resource.Error("Invalid User ID. It must be 2 uppercase letters followed by 5 digits.")
            return
        }

        if (!AuthInputValidator.isValidPassword(password)) {
            _registerViewState.value = Resource.Error("Invalid Password. It must be 8+ characters and include uppercase, lowercase, number, and special character.")
            return
        }

        if (!isValidName(name)) {
            _registerViewState.value = Resource.Error("Invalid name. Please enter a valid name.")
            return
        }

        viewModelScope.launch {
            _registerViewState.value = Resource.Loading

            repository.register(
                RegisterRequest(
                    userId = id,
                    password = password,
                    name = name,
                    dateOfBirth = date,
                    commandId = commandId
                )
            ).collect { result ->
                _registerViewState.value = when (result) {
                    is ResultWrapper.Success -> Resource.Success(Unit)
                    is ResultWrapper.GenericError -> Resource.Error(result.error ?: "Unknown error")
                    is ResultWrapper.NetworkError -> Resource.Error("Network error")
                }
            }
        }
    }

    fun setStateIdle(){
        _registerViewState.value= Resource.Idle
    }

    private fun isValidName(name: String): Boolean {
        return name.length >= 3 && name.matches(Regex("^[a-zA-Z\\s]+\$"))
    }



    fun fetchCommands(){
        viewModelScope.launch {
            _registerViewState.value= Resource.Loading
            repository.getCommands().collect { result->
                if (result is ResultWrapper.Success) {
                    _registerViewState.value= Resource.Idle
                    _commands.value = result.value
                } else {
                    _registerViewState.value= Resource.Error("Unable to fetch commands")
                }
            }
        }
    }
}