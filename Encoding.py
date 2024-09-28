import struct

def split_file_with_header(file_path, chunk_size=32):
    with open(file_path, 'rb') as file:
        chunk_number = 0
        send_to_data = [[0,0,0]]
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            
            chunk_size_bytes = struct.pack('H', len(chunk))  # H is short 2 bytes for size
            chunk_number_bytes = struct.pack('H', chunk_number)  # 2 bytes for order
            next_IP_Address = struct.pack('I', chunk_number) #4B for iP address
            next_Port = struct.pack('H',chunk_number)
            # Combine the header and the chunk
            header = chunk_size_bytes + chunk_number_bytes +next_IP_Address +next_Port
            data_with_header = header + chunk
            
            # Save each chunk with the header into a separate file
            with open(f'chunk_{chunk_number}', 'wb') as chunk_file:
                chunk_file.write(data_with_header)
            
            chunk_number += 1   
            newList = [[data_with_header,next_IP_Address,next_Port]]
            send_to_data= appendList(send_to_data,newList)
    return send_to_data

def appendList(l,element):
    l.append(element)
    return l

# Example usage
split_file_with_header('fun.txt')


