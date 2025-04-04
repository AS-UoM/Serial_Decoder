#Start of skeleton code
#Q1 Answer: There are 720 complete data frames in the file.
#Q2 Answer: There are 13 corrupt data frames in the file.
#Q3 Answer: The calendar date of these messages is 9th August 2003.

#Imports
import csv
import datetime

#Variables
buffer_frame = [] #Used to store each frame temporarily to decode it
frame_list = [] #Used to store all completed frames
STX_count = 0 #Used to track number of STX values in a row
#Set of counters used to track frame counts
complete_frame_counter = 0
incomplete_frame_counter = 0
uncorrupt_frame_counter = 0
corrupt_frame_counter = 0

#toString function for byte value to string conversion
def toString(byte):
    return str(int.from_bytes(byte, "big"))

#Open the binary input file
input_file = open("binaryFileC_84.bin", 'rb')

#Creates an empty csv output file, clears the contents of any existing output file
with open('decoded.csv', 'w', newline = '') as file:
    pass


#Read the first byte and loop as long as
#there is always another byte available
byte = input_file.read(1)
while byte:

    """
    The main logic of this program reads the data byte-by-byte, building up
    each frame, saving the complete frames and discarding the incomplete frames.
    It checks for corruption for each complete frame and stores each complete frame
    in a list to be used when outputting to a CSV file. It also tracks these 
    statistics whilst decoding the data.
    """

    #If '%' is read or the buffer frame isn't empty
    if (toString(byte) == "37") or buffer_frame:

        #If the buffer already contains 2 '%'s, check for 2 '%'s
        if (toString(byte) == "37") and (len(buffer_frame) > 2):
            STX_count += 1

            #One instance of '%' value (37), could just be value 37
            if STX_count == 1:
                buffer_frame.append(byte)

            #Two consecutive instances of '%' value (37)
            elif STX_count == 2:
                STX_count = 0

                #Reached new frame, check size of current frame
                frame_size = len(buffer_frame)

                #Frame size compared with expected value
                if frame_size != 27:
                    #Increment incomplete frame total
                    incomplete_frame_counter += 1
                    #Discard incomplete frame by emptying buffer
                    buffer_frame = []
                    #Add both '%' to buffer to start the new frame
                    buffer_frame.append(byte)
                    buffer_frame.append(byte)

                elif frame_size == 27:
                    #Increment complete frame total
                    complete_frame_counter += 1
                
                    #Process checksum for complete frame
                    checksum = 0
                    #Each element in the frame is summed
                    for value in range(26):
                        checksum = checksum + int.from_bytes(buffer_frame[value], "big")
                    #Both '%' and CHKSUM values are removed from the calculated checksum
                    checksum = checksum - 37 - 37 - int.from_bytes(buffer_frame[25], "big")
                    checksum = checksum % 256
                    checksum = 255 - checksum

                    #If the calculated checksum matches CHKSUM, increment uncorrupt frame counter
                    if checksum == int.from_bytes(buffer_frame[25], "big"):
                        uncorrupt_frame_counter += 1
                    #If the calculated checksum doesn't match CHKSUM, increment corrupt frame counter
                    elif checksum != int.from_bytes(buffer_frame[25], "big"):
                        corrupt_frame_counter += 1
                    #Add complete frame to list of frames, removing extra '%'
                    buffer_frame.pop(26)
                    frame_list.append(buffer_frame)
                    #Empty buffer for new frame
                    buffer_frame = []
                    #Add new '%' to buffer to start the new frame
                    buffer_frame.append(byte)
                    buffer_frame.append(byte)

        
        #If any value other than '%' is read, add it to the buffer
        else:
            #Add data to frame buffer and reset STX counter
            STX_count = 0
            buffer_frame.append(byte)

    #Get the next byte from the file and repeat
    byte = input_file.read(1)


#After decoding all complete frames, process each frame for output
for frame in frame_list:
        STX1 = '~'
        STX2 = '~'
        SYS_ID = int.from_bytes(frame[2], "big")
        DEST_ID = int.from_bytes(frame[3], "big")
        COMP_ID = int.from_bytes(frame[4], "big")
        SEQ = int.from_bytes(frame[5], "big")
        TYPE = int.from_bytes(frame[6], "big")
        PTX = chr(int.from_bytes(frame[7], "big"))

        #RPM, VLT and CRT are obtained from combining relevant bytes
        RPM = (int.from_bytes(frame[8], "big") << 8) | int.from_bytes(frame[9], "big")
        VLT = (int.from_bytes(frame[10], "big") << 8) | int.from_bytes(frame[11], "big")
        CRT = (int.from_bytes(frame[13], "big") << 8) | int.from_bytes(frame[12], "big")

        #Convert CRT to negative signed value if unsigned value is greater than 32767
        if CRT > 32767:
            CRT = (int.from_bytes(frame[13], "big") << 8) | int.from_bytes(frame[12], "big") - 65536
        
        #Temperatures calculated according to equation: 30 + (Byte_Value - 0xA0)*0.1
        MOS_TMP = 30 + ((int.from_bytes(frame[14], "big") - 160)*0.1)
        if (MOS_TMP < 30) or (MOS_TMP > 36.3):
            MOS_TMP = 0.0
        CAP_TMP = 30 + ((int.from_bytes(frame[15], "big") - 160)*0.1)
        if (CAP_TMP < 30) or (CAP_TMP > 36.3):
            CAP_TMP = 0.0

        TTX = chr(int.from_bytes(frame[16], "big"))

        #TME obtained by combining B0-B7 values to create 64-bit unsigned integer
        TME = (
            (int.from_bytes(frame[17], "big") << 56) | 
            (int.from_bytes(frame[18], "big") << 48) | 
            (int.from_bytes(frame[19], "big") << 40) |
            (int.from_bytes(frame[20], "big") << 32) |
            (int.from_bytes(frame[21], "big") << 24) |
            (int.from_bytes(frame[22], "big") << 16) |
            (int.from_bytes(frame[23], "big") << 8) |
            (int.from_bytes(frame[24], "big"))
        )

        CHKSUM = int.from_bytes(frame[25], "big")

        #Output frame created for writing to CSV file
        frame_set_entry = [STX1 + STX2, SYS_ID, DEST_ID, COMP_ID,
                           SEQ, TYPE, PTX, RPM, VLT, CRT,
                           MOS_TMP, CAP_TMP, TTX, TME, CHKSUM
                           ]
        
        #Opens output CSV in append mode to add frame to existing CSV file
        with open('decoded.csv', 'a', newline = '') as file:
            output_write = csv.writer(file)
            output_write.writerow(frame_set_entry)


#Must be end of the file so close the file
print("End of file reached")
input_file.close()

#Data statistics:
print("Number of complete frames: ", complete_frame_counter)
print("Number of incomplete frames:", incomplete_frame_counter)
print("Number of uncorrupt frames: ", uncorrupt_frame_counter)
print("Number of corrupt frames:", corrupt_frame_counter)

#Calculation of date using last TME value with conversion of microseconds to seconds
date_written = datetime.datetime.fromtimestamp(frame_set_entry[13]/1e6)
print("Date Written:", date_written)

#End of skeleton code
