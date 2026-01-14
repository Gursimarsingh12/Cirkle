package com.app.cirkle.domain.model.user

data class Interest(
    val id:Int,
    val name:String,
    var checked:Boolean=false
)