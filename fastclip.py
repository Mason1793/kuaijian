import imageio
import cv2
import numpy as np
import random
import time
import os
from utils import detect_image_4_results, get_classes
from model.yolo_model import YOLO

global yolo_model, classes_file, all_classes
yolo_model = None
classes_file = None
all_classes = None

def synthetize_Video_Mp3(video, voice, output):
    cmd = "ffmpeg -y -i " + voice + " -i " + video + " -vcodec h264 " + output
    os.system(cmd)


def convert_2_h264(video, output):
    cmd = "ffmpeg -y -i " + video + " -vcodec h264 " + output
    os.system(cmd)



def processing_random_time_interval(main_view_videocap, whole_view_videocap, output_videowriter, fps, length):
    """processing with random time interval for FastClip 0.0.1.

    # Argument:
        main_view_videocap: the main view video capture.
        whole_view_videocap: the whole view video capture.
        output_videowriter: the output video writer.
        fps: the fps of the video.
        length: the total amount of frames of the video.

    # Returns:
        int: tag for success or error.
        0: Fastclip succeed!
        1: Error: wrong filename!
        2: Error: different fps!
        3: Error: different resolution!
        4: Error: different length!
        5: Error: read frame error!
        6: Error: the video is too short, which is less than 20s!
    """

    total_processed_frame_count = 0
    left_length = length

    #################################### stage 0 ####################################
    # Start: Output whole view 10s

    beginning_length = 10
    for i in range(fps * beginning_length):
        # read frame
        success_main, frame_main = main_view_videocap.read()
        success_whole, frame_whole = whole_view_videocap.read()
        if success_main and success_whole != True:
            return 5

        # write to video
        output_videowriter.write(frame_whole)

        # accumulate processed frame count and left length
        total_processed_frame_count += 1
        left_length -= 1
        print(total_processed_frame_count)

    #################################### stage 1 ####################################
    # Alternative view

    tail_length = 10
    while left_length > fps * tail_length:

        # random length
        random_length_main = random.randrange(5 * fps, 20 * fps, fps)
        random_length_whole = random.randrange(5 * fps, 20 * fps, fps)
        
        # check length
        if left_length - random_length_main < fps * tail_length:
            random_length_main = left_length - fps * tail_length
            random_length_whole = 0
        elif left_length - random_length_main - random_length_whole < fps * tail_length:
            random_length_whole = left_length - random_length_main - fps * tail_length

        # clip main view
        print("main")
        while random_length_main > 0:
            # read frame
            success_main, frame_main = main_view_videocap.read()
            success_whole, frame_whole = whole_view_videocap.read()
            if success_main and success_whole != True:
                return 5

            # write to video
            output_videowriter.write(frame_main)

            # accumulate processed frame count and left length
            total_processed_frame_count += 1
            left_length -= 1
            random_length_main -= 1
            print(total_processed_frame_count)

        # clip whole view
        print("whole")
        while random_length_whole > 0:
            # read frame
            success_main, frame_main = main_view_videocap.read()
            success_whole, frame_whole = whole_view_videocap.read()
            if success_main and success_whole != True:
                return 5

            # write to video
            output_videowriter.write(frame_whole)

            # accumulate processed frame count and left length
            total_processed_frame_count += 1
            left_length -= 1
            random_length_whole -= 1
            print(total_processed_frame_count)

    #################################### stage 2 ####################################
    # End: Output whole view 10s
    
    while left_length > 0:
        # read frame
        success_main, frame_main = main_view_videocap.read()
        success_whole, frame_whole = whole_view_videocap.read()
        if success_main and success_whole != True:
            return 5

        # write to video
        output_videowriter.write(frame_whole)

        # accumulate processed frame count and left length
        total_processed_frame_count += 1
        left_length -= 1
        print(total_processed_frame_count)

    #################################################################################
    
    return 0


def processing_YOLOv3(main_view_videocap, whole_view_videocap, output_videowriter, fps, length, 
                    yolo_object_threshold = 0.6, yolo_nms_threshold = 0.5, visible = False):
    """processing with YOLOv3 for FastClip 0.0.2.

    # Argument:
        main_view_videocap: the main view video capture.
        whole_view_videocap: the whole view video capture.
        output_videowriter: the output video writer.
        fps: the fps of the video.
        length: the total amount of frames of the video.
        yolo_object_threshold: threshold for object.
        yolo_nms_threshold: threshold for non maximum suppression.

    # Returns:
        int: tag for success or error.
        0: Fastclip succeed!
        1: Error: wrong filename!
        2: Error: different fps!
        3: Error: different resolution!
        4: Error: different length!
        5: Error: read frame error!
        6: Error: the video is too short, which is less than 20s!
    """

    total_processed_frame_count = 0
    left_length = length

    # Initialize YOLOv3
    global yolo_model, classes_file, all_classes
    if yolo_model == None:
        yolo_model = YOLO(yolo_object_threshold, yolo_nms_threshold)
        classes_file = 'data/coco_classes.txt'
        all_classes = get_classes(classes_file)

    #################################### stage 0 ####################################
    # Start: Output whole view 10s

    beginning_length = 10
    for i in range(fps * beginning_length):
        # read frame
        success_main, frame_main = main_view_videocap.read()
        success_whole, frame_whole = whole_view_videocap.read()
        if success_main and success_whole != True:
            return 5

        # write to video
        output_videowriter.write(frame_whole)

        # visible
        if visible:
            cv2.imshow("test", frame_whole)
            if cv2.waitKey(10) & 0xff == 27:
                break

        # accumulate processed frame count and left length
        total_processed_frame_count += 1
        left_length -= 1
        print(total_processed_frame_count)

    #################################### stage 1 ####################################
    # Alternative view

    # State to check whether the whole view could alter to main view
    # Condition: main view has a person (p >= 0.90) and maintain this not less than 3 frames
    # That means there is a sliding window of 3 frames
    main_view_has_person_state = False
    
    # Read and detect window 0
    window_0_state = False
    success_main, frame_main_0 = main_view_videocap.read()
    success_whole, frame_whole_0 = whole_view_videocap.read()
    boxes0, classes0, scores0 = detect_image_4_results(frame_main_0, yolo_model, all_classes)
    if classes0 is not None:
        if classes0[0] == 0 and scores0[0] >= 0.90:
            window_0_state = True

    # Read and detect window 1
    window_1_state = False
    success_main, frame_main_1 = main_view_videocap.read()
    success_whole, frame_whole_1 = whole_view_videocap.read()
    boxes1, classes1, scores1 = detect_image_4_results(frame_main_1, yolo_model, all_classes)
    if classes1 is not None:
        if classes1[0] == 0 and scores1[0] >= 0.90:
            window_1_state = True

    # Read and detect window 2
    window_2_state = False
    success_main, frame_main_2 = main_view_videocap.read()
    success_whole, frame_whole_2 = whole_view_videocap.read()
    boxes2, classes2, scores2 = detect_image_4_results(frame_main_2, yolo_model, all_classes)
    if classes2 is not None:
        if classes2[0] == 0 and scores2[0] >= 0.90:
            window_2_state = True

    # check reading state
    if success_main and success_whole != True:
        return 6

    # change window state
    main_view_has_person_state = window_0_state and window_1_state and window_2_state
    print("state:", main_view_has_person_state)

    tail_length = 10
    while left_length > fps * tail_length:

        random_length_main = random.randrange(5 * fps, 10 * fps, fps)
        random_length_whole = random.randrange(10 * fps, 20 * fps, fps)
        
        # if left whole video is too short
        if left_length <= fps * tail_length + random_length_main:
            break

        print("Main begin:")
        # main view
        main_view_count = 0
        while main_view_count < random_length_main and left_length > fps * tail_length:
            
            # output
            output_videowriter.write(frame_main_0)
            main_view_count += 1
            
            # visible
            if visible:
                cv2.imshow("test", frame_main_0)
                if cv2.waitKey(10) & 0xff == 27:
                    break

            # update state
            frame_main_0 = frame_main_1
            frame_whole_0 = frame_whole_1
            window_0_state = window_1_state
            frame_main_1 = frame_main_2
            frame_whole_1 = frame_whole_2
            window_1_state = window_2_state
            
            success_main, frame_main_2 = main_view_videocap.read()
            success_whole, frame_whole_2 = whole_view_videocap.read()
            boxes2, classes2, scores2 = detect_image_4_results(frame_main_2, yolo_model, all_classes)
            window_2_state = False
            if classes2 is not None:
                if classes2[0] == 0 and scores2[0] >= 0.90:
                    window_2_state = True
            main_view_has_person_state = window_0_state and window_1_state and window_2_state
            print("state:", main_view_has_person_state)

            # accumulate processed frame count and left length
            total_processed_frame_count += 1
            left_length -= 1
            print(total_processed_frame_count)
            print("Main\n")

            if main_view_count >= fps * 5 and main_view_has_person_state == False:
                break

        # whole view
        print("Whole begin:")
        whole_view_count = 0
        while left_length > fps * tail_length:

            # output
            output_videowriter.write(frame_whole_0)
            whole_view_count += 1
            
            # visible
            if visible:
                cv2.imshow("test", frame_whole_0)
                if cv2.waitKey(10) & 0xff == 27:
                    break

            # update state
            frame_main_0 = frame_main_1
            frame_whole_0 = frame_whole_1
            window_0_state = window_1_state
            frame_main_1 = frame_main_2
            frame_whole_1 = frame_whole_2
            window_1_state = window_2_state
            
            success_main, frame_main_2 = main_view_videocap.read()
            success_whole, frame_whole_2 = whole_view_videocap.read()
            boxes2, classes2, scores2 = detect_image_4_results(frame_main_2, yolo_model, all_classes)
            window_2_state = False
            if classes2 is not None:
                if classes2[0] == 0 and scores2[0] >= 0.90:
                    window_2_state = True
            main_view_has_person_state = window_0_state and window_1_state and window_2_state
            print("state:", main_view_has_person_state)

            # accumulate processed frame count and left length
            total_processed_frame_count += 1
            left_length -= 1
            print(total_processed_frame_count)
            print("Whole\n")

            if whole_view_count > random_length_whole and main_view_has_person_state == True:
                break


    #################################### stage 2 ####################################
    # End: Output whole view 10s
    
    # output the surplus frames
    output_videowriter.write(frame_whole_0)
    output_videowriter.write(frame_whole_1)
    output_videowriter.write(frame_whole_2)
    
    # read new frame
    success_main, frame_main = main_view_videocap.read()
    success_whole, frame_whole = whole_view_videocap.read()
    if success_main and success_whole != True:
        return 5

    while left_length > 0:
        
        # write to video
        output_videowriter.write(frame_whole)
        
        # visible
        if visible:
            cv2.imshow("test", frame_whole)
            if cv2.waitKey(10) & 0xff == 27:
                break
        
        # read frame
        success_main, frame_main = main_view_videocap.read()
        success_whole, frame_whole = whole_view_videocap.read()
        if success_main and success_whole != True:
            return 5


        # accumulate processed frame count and left length
        total_processed_frame_count += 1
        left_length -= 1
        print(total_processed_frame_count)

    output_videowriter.write(frame_whole)

    #################################################################################
    
    return 0


def FastClip(main_view_filename, whole_view_filename, output_filename):
    """FastClip.

    # Argument:
        main_view_filename: the main view video.
        whole_view_filename: the whole view video.
        output_filename: name of output video.

    # Returns:
        int: tag for success or error.
        0: Fastclip succeed!
        1: Error: wrong filename!
        2: Error: different fps!
        3: Error: different resolution!
        4: Error: different length!
        5: Error: read frame error!
        6: Error: the video is too short, which is less than 20s!
    """

    # bulid video capture
    main_view_videocap = cv2.VideoCapture(main_view_filename)
    whole_view_videocap = cv2.VideoCapture(whole_view_filename)

    # check for right video
    if main_view_videocap.isOpened() and whole_view_videocap.isOpened() != True:
        return 1

    # show FPS
    print("\n---------------------------- Frame Per Second ----------------------------")
    main_view_fps = int(main_view_videocap.get(cv2.CAP_PROP_FPS))
    whole_view_fps = int(whole_view_videocap.get(cv2.CAP_PROP_FPS))
    print("Main view fps:", main_view_fps)
    print("Whole view fps:", whole_view_fps)
    print("--------------------------------------------------------------------------\n")
    if main_view_fps != whole_view_fps:
        return 2

    # show resolution
    print("\n------------------------------- Resolution -------------------------------")
    main_view_resolution = (int(main_view_videocap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(main_view_videocap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    whole_view_resolution = (int(whole_view_videocap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(whole_view_videocap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    print("Main view resolution:", main_view_resolution)
    print("Whole view resolution:", whole_view_resolution)
    print("--------------------------------------------------------------------------\n")
    if main_view_resolution != whole_view_resolution:
        return 3

    # show length
    print("\n--------------------------------- Length ---------------------------------")
    main_view_length = int(main_view_videocap.get(cv2.CAP_PROP_FRAME_COUNT))
    whole_view_length = int(whole_view_videocap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("Main view length:", main_view_length)
    print("Whole view length:", whole_view_length)
    print("--------------------------------------------------------------------------\n")
    if main_view_length != whole_view_length:
        return 4

    # check whether the length is enough for fastclip
    if main_view_length < main_view_fps * 30:
        return 6

    # bulid video writer
    output_videowriter = cv2.VideoWriter(output_filename, cv2.VideoWriter_fourcc("X","V","I","D"), int(main_view_fps), main_view_resolution)

    clip_result_status = processing_YOLOv3(main_view_videocap, whole_view_videocap, output_videowriter, main_view_fps, main_view_length)

    output_videowriter.release()
    main_view_videocap.release()
    whole_view_videocap.release()
    return clip_result_status


if __name__ == "__main__":

    start_time = time.time()

    main_view_filename = '/Users/mason/PycharmProjects/kuaijian/static/upload/1558938869423473.mp4'  # closer view
    whole_view_filename = '/Users/mason/PycharmProjects/kuaijian/static/upload/1558938869423473.mp4'    # further view
    output_filename = '/Users/mason/PycharmProjects/kuaijian/static/output/mai.mp4'

    result_tag = FastClip(main_view_filename, whole_view_filename, output_filename)

    if result_tag == 0:
        print("\nFastclip succeed!\n")
    elif result_tag == 1:
        print("\nError: wrong filename!\n")
    elif result_tag == 2:
        print("\nError: different fps!\n")
    elif result_tag == 3:
        print("\nError: different resolution!\n")
    elif result_tag == 4:
        print("\nError: different length!\n")
    elif result_tag == 5:
        print("\nError: read frame error!\n")
    elif result_tag == 6:
        print("\nError: the video is too short, which is less than 30s!\n")

    print("Total cost:", (time.time() - start_time), "s")