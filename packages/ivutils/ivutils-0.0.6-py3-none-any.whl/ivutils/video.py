import cv2
from . import image as img

class TaskStep:
    def apply(self, frame):
        pass
    def calc_dims(self)->tuple[int,int]:
        return -1, -1

class CropStep(TaskStep):
    def __init__(self, top, bottom, left, right):
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    def calc_dims(self):
        return self.right - self.left, self.bottom - self.top

    def apply(self, frame):
        return img.crop_image_array(frame, self.top, self.bottom, self.left, self.right)

class ResizeTask(TaskStep):
    def __init__(self, resize_dim: tuple[int,int]):
        self.resize_dim = resize_dim

    def calc_dims(self):
        return self.resize_dim

    def apply(self, frame):
        return img.resize_image_array(frame,self.resize_dim)


def get_file_handle(filename: str) -> cv2.VideoCapture:
    return cv2.VideoCapture(filename)


def release_file_handle(handle: cv2.VideoCapture):
    if handle is not None:
        handle.release()


def get_details(handle: cv2.VideoCapture) -> tuple[int, int, int, float]:
    """
    Returns a tuple of length, width, height, fps
    :param handle:
    :return:
    """
    length = int(handle.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(handle.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(handle.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = handle.get(cv2.CAP_PROP_FPS)
    return length, width, height, fps


def convert_sec(timestamp: str):
    """
    Convert a video timestamp (HH:MM:SS or MM:SS) to seconds.

    Args:
        timestamp (str): Timestamp in the format HH:MM:SS or MM:SS.

    Returns:
        int: Timestamp in seconds.
    """
    parts = list(map(int, timestamp.split(':')))

    if len(parts) == 3:
        # Format is HH:MM:SS
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        # Format is MM:SS
        minutes, seconds = parts
        return minutes * 60 + seconds
    elif len(parts) == 1:
        # Format is just SS
        return parts[0]
    else:
        raise ValueError("Invalid timestamp format. Use HH:MM:SS or MM:SS")


def task_transform(
        src_filename:str,
        trg_filename: str,
        start_frame:int = None,
        end_frame:int = None,
        start_time: str = None,
        end_time: str = None,
        frame_interval: int = 1,
        trans_steps:list[TaskStep]=None
):

    def time_to_frame(time_val, frame_id, default_frame, fps):
        if frame_id:
            return frame_id
        if not time_val:
            return default_frame
        elif ":" in time_val:
            time_val = convert_sec(time_val)

        frame_id = int(round(time_val * fps))
        return frame_id

    if trans_steps is None:
        trans_steps = []

    src_vid = None
    trg_vid = None

    try:
        src_vid = get_file_handle(src_filename)
        src_max_frames, src_frame_width, src_frame_height, src_fps = get_details(src_vid)

        start_frame = time_to_frame(start_time, start_frame, 0, src_fps)
        end_frame = time_to_frame(end_time, end_frame, src_max_frames, src_fps)

        assert (0 <= start_frame <= end_frame <= src_max_frames), f"Invalid range of start_frame: {start_frame} to end_frame: {end_frame}"

        new_width = src_frame_width
        new_height = src_frame_height

        if trans_steps:
            new_width, new_height = trans_steps[-1].calc_dims()

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        trg_vid = cv2.VideoWriter(trg_filename, fourcc, src_fps, (new_width, new_height))

        curr_frame = start_frame
        src_vid.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        while True:
            ret, frame = src_vid.read()

            # Break loop if frame is not read successfully
            if not ret or curr_frame >= end_frame:
                break

            curr_frame += 1

            if curr_frame % frame_interval == 0:
                for step in trans_steps:
                    frame = step.apply(frame)
                trg_vid.write(frame)

    finally:
        if src_vid: release_file_handle(src_vid)
        if trg_vid: trg_vid.release()
