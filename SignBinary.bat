@echo off

rem Now the command to actually sign the published binary file. Update the location of signtool.exe to the Win SDK Installation path.
rem signtools.exe comes as part of Windows SDK. Usually installed at "C:\Windows Kits\10\App Certification^ Kit\" for windows 10.
rem Time Stamping reference taken from https://gist.github.com/Manouchehri/fd754e402d98430243455713efada710

rem You need to make following three changes to this file befor running it in command prompt.
rem 1. Find the actual location of signtool.exe in your PC and udpate the line 14 accordingly.
rem 2. Change the actual name of .pfx file. in line 17
rem 3. Change the "your_pfx_password" to the actual password of pfx file you used to generate they code signing certificate.
rem 4. Actual path of your binary file in line 23
rem Provide the password of the pfx file on the /p line. i.e.  /p "typepasswordhere" ^

rem Set the actual location of signtool.exe in hard drive. Two such examples are following.
rem C:\"Windows Kits"\10\"App Certification Kit"\signtool.exe ^
rem C:\"Program Files (x86)\Windows Kits\10\App Certification Kit"\signtool.exe ^

C:\"Program Files (x86)\Windows Kits\10\App Certification Kit"\signtool.exe ^
sign /v ^
/fd SHA256 ^
/f CodeSigner-01.pfx ^
/p "your_pfx_password" ^
/tr "http://rfc3161timestamp.globalsign.com/advanced" ^
/td SHA256 ^
/du "https://example.com/" ^
/d "Your Software Name, Version: 1.0.0.0, Commit: ________" ^
.\YourBinaryFile.exe 

rem Upto above line. Make sure to revert the password change. THE PASSWORD MUST NOT BE COMMIT TO GIT.
rem Latteron, we may use the python itself to sign the binary.
rem However we will need a library which can correctly parse binary files! So delegate this to microsoft signtool.exe
