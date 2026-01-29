import ivutils.video as vid

class Tasks:
    TRANSFORM = "transform"

def get_parser(parent_parser):
    vid_command_parser = parent_parser.add_parser('vid', help='Video module')

    vid_tasks = vid_command_parser.add_subparsers(dest='task', help='Video tasks', required=True)

    # Resize Parser
    tran_parser = vid_tasks.add_parser(Tasks.TRANSFORM, help='Transforms a video clip')
    tran_parser.add_argument('-s', '--source', required=True, type=str,
                               help='Path to the source image file')
    tran_parser.add_argument('-t', '--target', required=True, type=str,
                               help='Path to save the resized image')
    tran_parser.add_argument('-sf', '--start_frame', required=False, type=int, default=0,
                               help='')
    tran_parser.add_argument('-ef', '--end_frame', required=False, type=int,
                               help='')
    tran_parser.add_argument('-st','--start_time', required=False, type=str, default=0,
                               help='')
    tran_parser.add_argument('-et','--end_time', required=False, type=str,
                               help='')
    tran_parser.add_argument('-fi','--frame_interval', required=False, type=int, default=1,
                               help='')
    tran_parser.add_argument('--resize_step', required=False, type=str,
                               help='Optional: format [width]x[height]')
    tran_parser.add_argument('--crop_step', required=False, type=str,
                               help='Optional: format [top]x[bottom]x[left]x[right]')
    return vid_command_parser


def process_parser(args):
    if args.task == Tasks.TRANSFORM:
        trans_steps = []

        if args.crop_step:
            top, bottom, left, right = map(int, args.crop_step.split('x'))
            trans_steps.append(vid.CropStep(top, bottom, left, right))

        if args.resize_step:
            new_width, new_height = map(int, args.resize_step.split('x'))
            trans_steps.append(vid.ResizeTask((new_width, new_height)))

        vid.task_transform(
            args.source,
            args.target,
            start_frame = args.start_frame,
            end_frame = args.end_frame,
            start_time = args.start_time,
            end_time = args.end_time,
            frame_interval = args.frame_interval,
            trans_steps=trans_steps)
    else:
        raise ValueError(f"Invalid task: {args.task}")
