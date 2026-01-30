![image](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)

# merl
An open-source useless python library that emulates (not fetches) some of Merl's most popular responses and answers. This may include some bonus ones that Merl does not actually say in the real thing, but come on who doesn't love a Minecraft Movie easter egg? Developed using the code.org IDE, because why not.
Use the following line on Windows to import merl:
```
pip install merl
```
If it says that 'pip.exe is blocked by group policy', try this:
```
python -m pip install --user merl
```
If THAT doesn't work, then give me some time to either fix my files or find another workaround.

---
To update Merl:
```
pip install --upgrade merl
```
Or do:
```
python -m pip install --upgrade --user merl
```

---
## Functions I want you to use
### send(pr)
Sends 'pr' to Merl where 'pr' is a string. The response automatically prints out in the terminal/IDE, so don't resize the window to less than the width of 40 characters wide. Otherwise the unprinting function breaks.

### sendRaw(pr)
Sends 'pr' to Merl where 'pr' is a string. The response is returned as a string, so its nicely paired with a *print()* statement, like this:

```Python
print(merl.sendRaw("Hello"))
```
Because it has no unprinting function, this function is less likely to break the terminal.

---
## Modes
**NOTE: THESE FEATURES DO NOT WORK ON ACTUAL MERL, JUST PYTHON MERL!**
### copyInput
To have Merl copy standard input to output, type "copyInput" in the send function, like this:

```Python
merl.send("copyInput")
```
This means that from now on, Merl will re-print whatever you put in send() until you tell them to stop using this:

### resetInputs
Simply type "resetInputs" to have them go back to normal! Like this:

```Python
merl.send("resetInputs")
```

---
## Example Program using send()
This is an exaple program (used by me) to test Merl's capabilities and features:
```Python
import merl
a = ""

while a != "!leave":
  a = input("<you> ")
  merl.send(a)
```



---
## Functions that are supposed to be hidden
### printanim(msg)
Prints 'msg' where 'msg' is a string. If 'msg' does not have spaces, then it all prints at once. Else, it prints word-by-word.
If 'msg' spans longer than the terminal's horizontal size, then it will start duplicating the messages with each line.
Keep each 'msg' short, like Merl!

### replyPrint(prompt)
Where 'prompt' is a string. This forces Merl to reply whatever, based on what you put in.
The reason why there are 3 "send" functions is because it has Merl check a thing or two before actually doing the reply checks, too.
Expect "I don't know." to show up more than once. With the exception of your system's time being between 9 AM and 4 PM, of course, because then you get a high traffic message more than actual answers! (If that's what you could call them)
