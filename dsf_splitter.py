import os
import sys 

# [  
#     ["FILE_NAME", ["TRACK_NAME", "TIME_START"], ["TRACK_NAME", "TIME_START"],
#
#     ["FILE_NAME", ["TRACK_NAME", "TIME_START"], ["TRACK_NAME", "TIME_START"]
# ] 

path = '\\'.join(sys.argv[1].split(sep='\\')[:-1]) + '\\'
new_dir_path = os.path.join(path, 'Splitted Tracks\\')

parsed_cue = []

with open(sys.argv[1], 'r') as file:
    state = (0,0,0,0)
    temp_cue, temp_index = [], []
    for line in file:
        line_1 = line
        line = [w for w in line.split()]
        if not len(line):
            continue
        if line[0] == 'FILE' or line[0] == 'TITLE':
            line = [w.strip() for w in line_1.split(sep='"')]
        if line[0] == 'FILE':
            assert(state == (0,0,0,0) or state == (1,1,1,1))
            if state == (1,1,1,1):
                parsed_cue.append(temp_cue)
                temp_cue = []
            state = (1,0,0,0)
            temp_cue.append(line[1])
        elif line[0] == 'TRACK':
            assert(state == (1,0,0,0) or state == (1,1,1,1))
            state = (1,1,0,0)
        elif line[0] == 'TITLE':
            if state == (0,0,0,0):
                continue
            assert(state == (1,1,0,0))
            state = (1,1,1,0)
            temp_index.append(line[1])
        elif line[0] == 'INDEX':
            assert(state == (1,1,1,0))
            state = (1,1,1,1)
            temp_index.append(line[2])
            temp_cue.append(temp_index)
            temp_index = []
    if len(temp_cue) > 1:
        parsed_cue.append(temp_cue)


#track_file[0] = "FILE_NAME"
#track_file[n] = ["TRACK_NAME", "TIME_START"]

os.mkdir(new_dir_path)

for track_file in parsed_cue:
    with open(path + track_file[0], 'rb') as file:
        header_1 = file.read(12)
        total_file_size_b = file.read(8)
        total_file_size = int.from_bytes(total_file_size_b, 'little')
        ID3v2 = file.read(8)
        ID3v2 = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        header_2 = file.read(24)
        channel_num_b = file.read(4)
        channel_num = int.from_bytes(channel_num_b, 'little')
        sampling_frequency_b = file.read(4)
        sampling_frequency = int.from_bytes(sampling_frequency_b, 'little')
        header_3 = file.read(4)
        sample_count = file.read(8)
        header_4 = file.read(12)
        sample_data_chunk_b = file.read(8)
        sample_data_chunk = int.from_bytes(sample_data_chunk_b, 'little')
        header_total_size = 92
        ms_size_b = int(sampling_frequency / 8 * channel_num / 100)
        bytes_remaining_to_read_write = sample_data_chunk
        for i, line in enumerate(track_file[1:]):
            m, s, ms = [int(i) for i in line[1].split(sep=':')]
            start_time = m * 6000 + s * 100 + ms
            bytes_to_write = 0
            if len(track_file) > i + 2:
                m_1, s_1, ms_1 = [int(i) for i in track_file[i+2][1].split(sep=':')]
                end_time = m_1 * 6000 + s_1 * 100 + ms_1
                bytes_to_write = (end_time - start_time) * ms_size_b
                bytes_to_write -= bytes_to_write % (4096 * channel_num)
            else:
                bytes_to_write = bytes_remaining_to_read_write
            bytes_remaining_to_read_write -= bytes_to_write
            new_file = open(new_dir_path + line[0] + '.dsf', 'wb')
            new_file.write(header_1 + (header_total_size + bytes_to_write).to_bytes(8, 'little')
                               + ID3v2 + header_2 + channel_num_b + sampling_frequency_b + header_3
                               + (bytes_to_write * 8 // channel_num).to_bytes(8, 'little')
                               + header_4 + (bytes_to_write + 12).to_bytes(8, 'little'))
            while bytes_to_write:
                if bytes_to_write > 4096:
                    new_file.write(file.read(4096))
                    bytes_to_write -= 4096
                else:
                    new_file.write(file.read(bytes_to_write))
                    bytes_to_write = 0
            new_file.close()
