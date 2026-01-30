#RLE/RLE.py

def RLE(input):
    if isinstance(input, list) == True or isinstance(input, str) == True or isinstance(input, bytes) == True:
        output = []
        current_char = None
        count = 0
        if len(input) < 6:
            raise Exception('Input is too short for RLE.')
        for i in range(len(input)):
            if i == 0:
                current_char = input[i]
                count += 1
            else:
                if current_char == input[i]:
                    count += 1
                else:
                    output.append(count)
                    output.append(current_char)
                    current_char = input[i]
                    count = 1
        output.append(count)
        output.append(current_char)
        return output
    else:
        raise Exception('Invalid input type for RLE. Requires List, Bytes or String type.')

