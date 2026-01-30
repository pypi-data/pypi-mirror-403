# Merl isn't the most intelligent AI, so to mimic that,
# I will fill them with a bit more... personality! Meet
# my Markov Chain Engine. Cool, isn't it?
# Of course, this only adds a *little* variation to
# Merl's responses, and even then some chains aren't
# perfect (looking at you, 'msg_pb'!).

import random

msg_blank = {
  "_init_" : [["1", "2"], [1, 1]],
  " S" : [[" o", " b"],[1, 1]],
  "a" : [["blank"], [1]]
}

msg_test_jackenstien = {
  "_init_" : [["YOUR", "YOU'RE"], [1, 1]],
  "YOUR" : [[" TAKING", " TOO", " LONG"], [3, 1, 1]],
  " TAKING" : [[" TOO"], [1]],
  " TOO" : [[" LONG!", " TOO!"], [2, 1]],
  "YOU'RE" : [[" TAKING", " TOO", " LONG"], [3, 1, 1]]
}

msg_pineapple = {
  "_init_" : [["I", "No, I"], [1, 1]],
  "I" : [[" hate", " don't like"],[1, 1]],
  "No, I" : [[" hate", " don't like"],[1, 1]],
  " hate" : [[" pineapples...", " pineapples!"],[1, 1]],
  " don't like" : [[" pineapples."], [1]]
}

# by the way i made these without using trees or diagrams on sheets of
# paper, so maybe that's why they're flawed.
# eh, i'll fix it in the next update. or not. i don't care right now!!

msg_update = {
  "_init_" : [["If you", "Do you", "Are you"], [8, 1, 8]],
  "If you" : [[" are asking about the next", " wish to know the next"],[1, 1]],
  " are asking about the next" : [[" update, prerelease, or preview, then", " update, then"],[1, 1]],
  " update, prerelease, or preview, then" : [[" sorry.", " I cannot answer that."],[4, 1]],
  " update, then" : [[" sorry. I don't know that yet.", " sorry, but I don't have the data available to see what it is."],[3, 1]],
  " wish to know the next" : [[" update, then"],[1]],
  " wishing to know the next" : [[" update? If so, I cannot provide that information yet. Is there anything else that I can help you with?"],[1]],
  "Do you" : [[" want to know about the next update? Because I do, too. I don't know what it is, but I'll gladly tell you all about it when it releases!", " want to die?"],[100, 1]], # do you want to die?
  "Are you" : [[" asking about the next", " wishing to know the next"],[1, 1]],
  " asking about the next" : [[" updates? Because I don't know about them either.", " versions/drops of Minecraft? Because I don't know about that, either."],[1, 4]],
  " want to die?" : [[" AGAIN?", "?"], [1, 100]]
}

msg_copy = {
  "_init_" : [["I'm sorry, but", "It appears that you are"], [1, 1]],
  "I'm sorry, but" : [[" as an AI assistant, I", " it appears that you are"],[3, 1]],
  "It appears that you are" : [[" intentionally", " copying"],[1, 2]],
  " it appears that you are" : [[" intentionally", " copying"],[2, 1]],
  " intentionally" : [[" copying"],[1]],
  " copying" : [[" me.", " my most frequent messages."],[1, 1]],
  " me." : [[" Is there"],[1]],
  " as an AI assistant, I" : [[" am designed to be", " cannot stand you."],[100, 1]],
  " am designed to be" : [[" your guide", " a helper for all your Minecraft needs."],[1, 1]],
  " a helper for all your Minecraft needs." : [[" Is there"],[1]],
  " your guide" : [[" to everything", " in regards", " for anything"],[2, 1, 2]],
  " to everything" : [[" related to", " Minecraft."],[1, 1]],
  " related to" : [[" Minecraft."],[1]],
  " in regards" : [[" to everything"],[1]],
  " to everything" : [[" related to Minecraft.", " Minecraft-related."],[1, 1]],
  " related to Minecraft." : [[" Is there"], [1]],
  " Minecraft-related." : [[" Is there"], [1]],
  " Is there" : [[" anything else you want me to", " any other way I could"],[1, 1]],
  " anything else you want me to" : [[" help with,"],[1]],
  " any other way I could" : [[" help?", " help,"],[1, 8]],
  " help with," : [[" besides being something to copy?", " besides being someone to copy?"],[8, 1]],
  " help," : [[" besides being something to copy?", " besides being someone to copy?"],[10, 1]]
}

msg_greet = {
  "_init_" : [["Hello", "Hi", "Greetings!", "..not YOU again."], [100, 100, 100, 1]],
  "Hello" : [[" there", "! I am Merl", "! I am M"],[6, 7, 1]],
  "! I am M" : [["M", "erl"],[9, 5]],
  "M" : [["M", "erl"],[19, 1]],
  "erl" : [[", your"],[1]],
  "Hi" : [[" there", "! I am Merl"],[1, 1]],
  "Greetings!" : [[" I am Merl", " My name is Merl"],[1, 1]],
  " there" : [[", I am Merl", "! I am Merl"],[1, 1]],
  ", I am Merl" : [[", your", ". How can I help you today"],[1, 1]],
  "! I am Merl" : [[", your", ". How can I help you today"],[1, 1]],
  " I am Merl" : [[", your", ". How can I help you today"],[1, 1]],
  " My name is Merl" : [[", your", ". How can I help you today"],[1, 1]],
  ", your" : [[" assistant for all things Minecraft", " AI-Powered"],[1, 1]],
  " AI-Powered" : [[" assistant for all things Minecraft"],[1]],
  " assistant for all things Minecraft" : [["!"],[1]],
  ". How can I help you today" : [[" on the topic of Minecraft?", "?"],[1, 1]]
}

msg_pb = {
  "_init_" : [["Are you", "If you", "Peanut"], [1, 1, 1]],
  "Are you" : [[" asking", " wanting to"],[1, 1]],
  " asking" : [[" about my", " for info on"],[1, 1]],
  " for info on" : [[" Peanut Butter", " my"],[1, 1]],
  " about my" : [[" cat", " pet"],[1, 1]],
  " wanting to" : [[" know more about my", " eat pizza?"],[100, 1]],
  "If you" : [["'re asking about", " want to know more about"],[1, 1]],
  "'re asking about" : [[" my", " Peanut Butter"],[1, 1]],
  " want to know more about" : [[" my", " Peanut Butter"],[1, 1]],
  " know more about my" : [[" cat", " pet"],[1, 1]],
  " my" : [[" cat", " pet"],[1, 1]],
  " pet" : [[" cat"],[1]],
  " cat" : [[" Peanut Butter"],[1]],
  " Peanut Butter" : [[", then sorry. ", ", because "],[1, 1]],
  ", then sorry. " : [["Peanut"],[1]],
  ", because " : [["Peanut", "%j"],[5, 1]],
  "%j" : [["Peanut", "%j"],[1, 8]],
  "Peanut" : [[" Butter is", " Butter died."],[1, 1]],
  " Butter is" : [[" no longer", " dead.", " is also an AI, like me!"],[3, 3, 1]],
  " no longer" : [[" with us.", " with me.", " alive.", " allowed here. Mojang is kinda cruel."],[6, 6, 6, 1]]
}

msg_movie = {
  "_init_": [["No.", "Sorry", "Nuh uh,"], [4, 2, 1]],
  "No." : [[" No"],[1]],
  " No" : [[" no", " no.", " no!"],[3, 1, 1]],
  " no" : [[" no", " no.", " no!"],[3, 1, 1]],
  " no." : [[" I am NOT", " I will NOT"],[1, 1]],
  " no!" : [[" I am NOT", " I will NOT"],[1, 1]],
  "Nuh uh," : [[" I am NOT", " I will NOT"],[1, 1]],
  " I am NOT" : [[" going to"],[1]],
  " going to" : [[" talk about"],[1]],
  " I will NOT" : [[" talk about"], [1]],
  " talk about" : [[" 'A Minecraft Movie'.", " the movie."],[1, 1]],
  "Sorry" : [[", but I don't", " about your"],[5, 1]],
  " about your" : [[" interest in", " stupid phase concerning"],[100, 1]],
  " interest in" : [[" 'A Minecraft Movie'.", " the movie."],[1, 1]],
  ", but I don't" : [[" feel like talking about", " want to"],[1, 1]],
  " want to" : [[" talk about"],[1]],
  " feel like talking about" : [[" 'A Minecraft Movie'.", " the movie."],[1, 1]]
}

def retmark(d: dict):
  final = ""
  cur = "_init_"
  while True:
    if cur in d.keys():
      cur = random.choices(d[cur][0], d[cur][1])[0]
      final = f"{final}{cur}"
    else: break
  return final
