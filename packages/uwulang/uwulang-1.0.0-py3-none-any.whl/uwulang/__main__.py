from sys import exit
def engToUwU(text: str) -> str:
    return text.lower().replace('l',  'w').replace('r', 'w').replace('k', 'w')
print('--- UwU Lang ---')
while True:
    try:
        print(engToUwU(input('>> ')))
    except KeyboardInterrupt:
        print('Bye!')
        exit()
