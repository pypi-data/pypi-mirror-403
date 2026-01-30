#RLD/RLD.py

def RLD(input):
    output = []
    if isinstance(input, list) == True:
        for i in range(1, len(input), 2):
            value = input[i]
            count = input[i-1]
            while count != 0:
                output.append(value)
                count -= 1
        return output
    else:
        raise Exception('Wrong input use list returned by RLE method')

