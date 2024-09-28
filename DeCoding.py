import struct

def read_chunks_with_header(file_name_pattern, total_chunks):
    original_data = b''
    chunk_number = 0
    while(True):
        file_name = file_name_pattern.format(chunk_number)
        try:
            with open(file_name, 'rb') as chunk_file:
                # Read the first 10 bytes (2 bytes for size and 2 bytes for order...)
                header = chunk_file.read(10)
                chunk_size, chunk_number_in_file,next_IP_Address,next_Port = struct.unpack('HHIH', header)  # 2 bytes for size, 2 for order
                
                # Verify chunk number if needed
                if chunk_number != chunk_number_in_file:
                    raise ValueError(f"Expected chunk {chunk_number} but found {chunk_number_in_file}.")

                # Read the actual chunk data
                chunk_data = chunk_file.read(chunk_size)
                
                # Append the chunk data to the original data
                original_data += chunk_data
                chunk_number += 1
        except:
            break
    return original_data

# Example usage
# Assuming the chunks are named "chunk_0", "chunk_1", ..., "chunk_N"
reconstructed_data = read_chunks_with_header('chunk_{}', total_chunks=30)

# Now you can do whatever you need with `reconstructed_data` (e.g., save it back to a file)
with open('reconstructed_file.txt', 'wb') as output_file:
    output_file.write(reconstructed_data)
