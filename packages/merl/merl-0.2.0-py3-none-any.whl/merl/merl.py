"""
THANK YOU FOR IMPORTING THE MOST USELESS MODULE EVER CREATED!
I hope you hate it!

---O9CreeperBoi

p.s. Hi, PhoenixSC!
"""

import time
import random
import re
import merlkov

CURSOR_UP = "\033[1A"
CLEAR = "\x1b[2K"
CLEAR_LINE = CURSOR_UP + CLEAR

match = 0
global result
result = 0
restring = ""

# math!
num = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "twenty one", "twenty two", "twenty three", "twenty four", "twenty five", "twenty six", "twenty seven", "twenty eight", "twenty nine", "thirty", "thirty one", "thirty two", "thirty three", "thirty four", "thirty five", "thirty six", "thirty seven", "thirty eight", "thirty nine", "fourty", "fourty one", "fourty two", "fourty three", "fourty four", "fourty five", "fourty six", "fourty seven", "fourty eight", "fourty nine", "fifty", "fifty one", "fifty two", "fifty three", "fifty four", "fifty five", "fifty six", "fifty seven"] # 57
ope = ["plus", "minus", "times", "divided by"]
# LMAO merl can only count up to 57 thats crazy.


# Oops! Can't have users cursing in MY module!
banned = [" ass", "pee", "poo", "fuc", "shi", "damn", " hell ", "nig", "bitc", "craft a", "kil", "unaliv", "die", "slas", "end update", "viola", "dam", "frick", "hecking", "sex", "nut", "virgin", "weed", "sucks", "sybau", "shut up", "shut it", "feral", "shish", "gang", "diarrhea"]

# in case ppl ask about the future!
future = ["update", "snapshot", "rerelea", "preview", "leak", "spoiler"]

# Peanut butter 💀
pb = ["peanut butter", "your cat", "pb", "earth cat"]

# Let's greet Merl!
greet = ["hi", "hello", "wassup", "whats up", "what's up", "whaddup", " yo ", "how are you doin", "how you doin", "greetings"]

# chicken jockey!
help = ["tell me", "help me", "help"]
cj = ["chicken jockey", "i am steve", "ender pearl", "boots of swiftness", "water bucket", "lava chicken", "the nether", "flint and steel", "crafting table"]

copyin = ["i dont know", "i don't know", "language that vi", "ing higher traff", "reword your"]

mine = ["cho minecr", "int minecr", "minecraft!", "say minecr", "ne plus tw"] # im such a troll

# hey merl what can you do
capable = ["you do anyt", "capab", "able", "calcul", "at can you"]

# don't ask what these do.
m = 0
num_pattern = "|".join(num)
ope_pattern = "|".join(ope)
pattern = rf"\b({num_pattern})\s+((?:{ope_pattern}))\s+({num_pattern})\b"

# every single reply possible that is not math related
reply = {
  "test":["This is a test for ", "Merl's dialogue. I can add and subtract!"],
  "cap":["I'm glad you asked! I can", " do basic math with numbers ", "up to fifty seven now. Go on, give ", "me a problem!"],
  "busy":["We are currently experiencing higher ", "traffic than expected. Please wait ", "a moment and resend your last ", "message."],
  "movie":["No. No no no. I am not here to talk ", "about the Minecraft Movie. Can you ", "ask me anything besides that?"],
  "copy":["I'm sorry, but I am designed to be a ", "guide for 'Minecraft', and not to be ", "copied. Can I help you with anything ", "else?"],
  "languageViolation":["Your previous message contains ", "language that violates our content ", "policy. Please reword your response."],
  "update":["If you are wishing to know the next ", "update, prerelease, or preview, then ", "sorry. I cannot provide that information ", "yet. Can I help you with something else?"],
  "pb":["Are you talking about my cat, Peanut ", "Butter? If so, then bad news. They ", "died a while ago. :_("],
  "iCanHelp":["I can help you with questions related ", "to Minecraft! What do you need ", "assistance with?"],
  "minecraft":["Minecraft!"], # Minecraft!
  "idk":["I don't know."], # I don't know.
  "greet":["Hello there! I am Merl, a support AI ", "made by Mojang. How can I help you ", "today on the topic of Minecraft?"],
  "idk2":["I don't know. Can I help you with a ", "question related to Minecraft?"],
  "englishOnly":["I can only provide support in ", "English right now. Can I help ", "you with a question related ", "to 'Minecraft'?"]
}

def checkmath(inp: str):
  num_map = {word: value for word, value in zip(num, range(len(num)))}
  match = re.search(pattern, inp)
  global restring
  if match:
    num1_word = match.group(1)
    ope_word = match.group(2)
    num2_word = match.group(3)

    num1 = num_map[num1_word]
    num2 = num_map[num2_word]
    global result
    result = None

    # calculation times uh9gsigohdfbiushegtfd equals great job thats right!!!
    if ope_word == "plus":
        result = num1 + num2
        restring = f"{num1} plus {num2} is {result}."
    elif ope_word == "minus":
        result = num1 - num2
        restring = f"{num1} minus {num2} is {result}."
    elif ope_word == "times":
        result = num1 * num2
        restring = f"{num1} times {num2} is {result}."
    elif ope_word == "divided by":
        if num2 != 0:
            result = num1 / num2
            restring = f"{num1} divided by {num2} equals {result}."
        else:
            restring = "It is not possible to divide by zero."
    else:
      restring = ""


def replyMsg(cate: str):
  a = ""
  for x in range(len(reply[cate])):
    a = f"{a}{reply[cate][x]}"
  return a

def markprintanim(msg: str):
  split_msg = msg.split()
  f = ""
  for x in range(len(split_msg)):
    f = f"{f} {split_msg[x]}"
    if x % 7 == 0: print(""); f = split_msg[x]
    print(CLEAR_LINE, f)
    time.sleep(0.1)

def printanim(msg: str):
  split_msg = msg.split()
  f = ""
  print("")
  for x in range(len(split_msg)):
    f = f"{f} {split_msg[x]}"
    print(CLEAR_LINE, f)
    time.sleep(0.1)

# this is what you send to nerl if you are simply pimply
def sendRaw(prompt: str):
  global result
  result = None
  checkmath(prompt)
  match = 0
  global m
  if prompt == "copyInput":
    m = 1
  if m == 1:
    if prompt == "resetInputs":
      m = 0
      print("Mode Reset")
    else:
      # copy standard input to standard output.
      print(prompt)
  else:
    # merl is yapping rn fr fr
    time_tuple = time.localtime()
    hour = time_tuple.tm_hour
    global pb, banned, greet, help, cj, copyin
    if hour >= 9 and hour <= 16 and random.randint(0, 16) < 4:
      return replyMsg("busy")
    else:
      if any(sub.lower() in prompt.lower() for sub in copyin): return merlkov.retmark(merlkov.msg_copy)
      elif any(sub.lower() in prompt.lower() for sub in banned): return replyMsg("languageViolation")
      elif any(sub.lower() in prompt.lower() for sub in capable): return replyMsg("cap")
      elif any(sub.lower() in prompt.lower() for sub in future): return merlkov.retmark(merlkov.msg_update)
      elif any(sub.lower() in prompt.lower() for sub in pb): return merlkov.retmark(merlkov.msg_pb)
      elif any(sub.lower() in prompt.lower() for sub in help): return replyMsg("iCanHelp") # can you really?
      elif any(sub.lower() in prompt.lower() for sub in mine): return replyMsg("minecraft")
      elif any(sub.lower() in prompt.lower() for sub in cj): return merlkov.retmark(merlkov.msg_movie)
      elif any(sub.lower() in prompt.lower() for sub in greet): return merlkov.retmark(merlkov.msg_greet)
      else:
        if result != None:
          return restring
        else:
          g = random.randint(0,7)
          if g == 1: return replyMsg("idk2")
          elif g == 2: return replyMsg("englishOnly")
          elif g == 5: return "I can't help with that." # seriously this one is new.
          else: return replyMsg("idk") # ha ha!


# this is what you send to berl if you are fancy pantsy
def send(pr: str):
  global m
  if pr == "copyInput":
    m = 1
  if m == 1:
    if pr == "resetInputs":
      m = 0
      print("Mode Reset")
    else:
      # copy standard input to standard output.
      print(pr)
  else:
    # ok fine. Merl wants to talk.
    replyPrint(pr)

# tree of importance
def replyPrint(prompt: str):
  global result
  result = None
  checkmath(prompt)
  time_tuple = time.localtime()
  hour = time_tuple.tm_hour
  global pb, banned, greet, help, cj, copyin
  if hour >= 9 and hour <= 16 and random.randint(0, 16) < 4:
    for x in range(len(reply["busy"])): printanim(reply["busy"][x])
  else:
    if any(sub.lower() in prompt.lower() for sub in copyin):
      markprintanim(merlkov.retmark(merlkov.msg_copy))
    elif any(sub.lower() in prompt.lower() for sub in banned):
      for x in range(len(reply["languageViolation"])): printanim(reply["languageViolation"][x])
    elif any(sub.lower() in prompt.lower() for sub in capable):
      for x in range(len(reply["cap"])): printanim(reply["cap"][x])
    elif any(sub.lower() in prompt.lower() for sub in future):
      markprintanim(merlkov.retmark(merlkov.msg_update))
    elif any(sub.lower() in prompt.lower() for sub in pb):
      markprintanim(merlkov.retmark(merlkov.msg_pb))
    elif any(sub.lower() in prompt.lower() for sub in help):
      for x in range(len(reply["iCanHelp"])): printanim(reply["iCanHelp"][x])
    elif any(sub.lower() in prompt.lower() for sub in mine):
      printanim("Minecraft!") # the thing that won't change.
    elif any(sub.lower() in prompt.lower() for sub in cj):
      markprintanim(merlkov.retmark(merlkov.msg_movie))
    elif any(sub.lower() in prompt.lower() for sub in greet):
      markprintanim(merlkov.retmark(merlkov.msg_greet))
    else:
      if result != None:
        printanim(restring)
      else:
        g = random.randint(0,7)
        if g == 1:
          for x in range(len(reply["idk2"])): printanim(reply["idk2"][x])
        elif g == 2:
          for x in range(len(reply["englishOnly"])): printanim(reply["englishOnly"][x])
        elif g == 3:
          printanim("I can't help with that.")
          # this one is new. they actually said this and idk why.
        else:
          # The statement to end all statements.
          # Behold. The one, the legend, the answer supreme...
          printanim("I don't know.")
          # This won't change, either.
    

