import ivutils.image as img

class Tasks:
    RESIZE = "resize"
    CROP = "crop"

def get_parser(parent_parser):
    img_command_parser = parent_parser.add_parser('img', help='Image module')

    img_tasks = img_command_parser.add_subparsers(dest='task', help='Image tasks', required=True)

    # Resize Parser
    resize_parser = img_tasks.add_parser(Tasks.RESIZE, help='Resize an image')
    resize_parser.add_argument('-s', '--source', required=True, type=str,
                               help='Path to the source image file')
    resize_parser.add_argument('-t', '--target', required=True, type=str,
                               help='Path to save the resized image')
    resize_parser.add_argument('-H', '--height', required=True, type=int,
                               help='Target canvas height in pixels')
    resize_parser.add_argument('-W', '--width', required=True, type=int,
                               help='Target canvas width in pixels')
    # Crop Parser
    crop_parser = img_tasks.add_parser(Tasks.CROP, help='Crop an image')
    crop_parser.add_argument('-s', '--source', required=True, type=str,
                             help='Path to the input image file')
    crop_parser.add_argument('-t', '--target', required=True, type=str,
                             help='Path where the cropped image will be saved')

    crop_parser.add_argument('--top', type=float, default=0.0, # Use float to support both 10 and 0.1
                             help='Top boundary. Positive int: absolute Y coord; '
                                  'Negative int: px to remove; Float (0-1): percentage')

    crop_parser.add_argument('--bottom', type=float, default=0.0,
                             help='Bottom boundary. Positive int: absolute Y coord; '
                                  'Negative int: px to remove from bottom; Float (0-1): percentage')

    crop_parser.add_argument('--left', type=float, default=0.0,
                             help='Left boundary. Positive int: absolute X coord; '
                                  'Negative int: px to remove; Float (0-1): percentage')

    crop_parser.add_argument('--right', type=float, default=0.0,
                             help='Right boundary. Positive int: absolute X coord; '
                                  'Negative int: px to remove from right; Float (0-1): percentage')

    return img_command_parser


def process_parser(args):
    if args.task == Tasks.RESIZE:
        resize_dim = (args.width, args.height)
        img.resize_image(args.source, args.target, resize_dim=resize_dim)
    elif args.task == Tasks.CROP:
        img.crop_image(
            args.source,
            args.target,
            top=args.top,
            bottom=args.bottom,
            left=args.left,
            right=args.right
        )
    else:
        raise ValueError(f"Invalid task: {args.task}")
