---
layout: post
title: VBA Portable Date
categories: [home, tech, VBA]
---

In Excel, the date format depends on the locale setting of the computer, e.g., the formula =TEXT(TODAY(),"YYYY-MM-DD") only works correctly on computers set to English locales, and =TEXT(HEUTE(),"JJJJ-MM-TT") works on computers with German locale settings. This makes worksheets with such functions not portable between computers with different locale settings.

This VBA macro adds =PORTABLE_TODAY() function, which fixes this problem and works on any computer. 

## Installation
In the worksheet, where you want to add this code, press **Alt+F11**, Press **Insert > Module** and paste the below code. Then save the worksheet and add the formula =PORTABLE_TODAY() wherever you require.

## Code
```vb
Public Function PORTABLE_TODAY()
    Dim monthString As String
    Dim dayString As String
    Dim month As Integer
    Dim day As Integer
    
    month = Int(DatePart("m", Now()))
    day = Int(DatePart("d", Now()))
    
    If month < 10 Then
        monthString = "0" & month
    Else
        monthString = month
    End If
    
    If day < 10 Then
        dayString = "0" & day
    Else
        dayString = day
    End If
    
    PORTABLE_TODAY = DatePart("yyyy", Now()) & "-" & monthString & "-" & dayString
End Function
```

Also available as a [gist](https://gist.github.com/PhilippMundhenk/17e780e2cbcdc054e48a3ad3e5faa13a).