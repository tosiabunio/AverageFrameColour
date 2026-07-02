#pip install list:
# pytubefix
# opencv-python
# pillow

from pytubefix import YouTube
import argparse
import cv2
import math
import os
import shutil
from PIL import Image, ImageStat, ImageDraw

#Get average colour of frames
def get_average_colour(image_name, colour_list, frame_folder):
  image = Image.open(frame_folder+"/"+image_name)
  average = ImageStat.Stat(image).mean
  colour_list.append(average)
  
def get_colour_list(download_folder, download_name, frame_folder):
  #Get frames from video (once every second)
  vidcap = cv2.VideoCapture(download_folder+"/"+download_name+".mp4")
  fps = vidcap.get(cv2.CAP_PROP_FPS)
  success,image = vidcap.read()
  count = 0
  colour_list = []
  while success:
    if count % round(fps) == 0:
      frame_name = "frame%d.jpg" % count
      cv2.imwrite(frame_folder+"/"+frame_name, image)     # save frame as JPEG file
      get_average_colour(frame_name, colour_list, frame_folder)
    success,image = vidcap.read()
    count += 1
  return colour_list

def image_scale(index, scale):
  return int(index * scale)

def get_frame_means(video_path):
  #Average colour of every frame, computed in memory (no JPEGs on disk)
  vidcap = cv2.VideoCapture(video_path)
  success,image = vidcap.read()
  means = []
  while success:
    blue, green, red = image.mean(axis=(0,1))[:3]
    means.append((red, green, blue))
    success,image = vidcap.read()
  return means

def resample_means(means, num_columns):
  #Map per-frame colours onto num_columns columns; works both when there are
  #more frames than columns (chunks get averaged) and fewer (frames stretch
  #across columns) — every column is backed by at least one frame
  total = len(means)
  columns = []
  for i in range(num_columns):
    start = i * total // num_columns
    end = max((i + 1) * total // num_columns, start + 1)
    chunk = means[start:end]
    columns.append(tuple(sum(channel) / len(chunk) for channel in zip(*chunk)))
  return columns

def pick_bar_count(frame_count, bar_width, max_bars=6):
  return min(max_bars, max(1, math.ceil(frame_count / bar_width)))

def render_bars(columns, n_bars, bar_width, bar_height):
  output_image = Image.new('RGB', (bar_width, n_bars * bar_height), color = 'white')
  d = ImageDraw.Draw(output_image)
  for index, value in enumerate(columns):
    x = index % bar_width
    top = (index // bar_width) * bar_height
    d.line((x, top, x, top + bar_height - 1), fill=(int(value[0]),int(value[1]),int(value[2])))
  return output_image

def parse_resolution(value):
  try:
    width, height = value.lower().split("x")
    return (int(width), int(height))
  except ValueError:
    raise argparse.ArgumentTypeError("resolution must be WIDTHxHEIGHT, e.g. 1920x1080")

def average_colours(video_url, mode="classic", resolution=(1920, 1080), output_file="output.png", show=True):
  download_folder = "cache"
  download_name = "test"
  frame_folder = os.path.join(download_folder,"frames")

  try:
    shutil.rmtree(download_folder)
  except FileNotFoundError:
    print(download_folder + " folder does not exist. Creating one!")

  #Make sure folders exist
  os.makedirs(download_folder, exist_ok=True)
  os.makedirs(frame_folder, exist_ok=True)

  #Download video
  print("downloading video...")
  video = YouTube(video_url)
  stream = video.streams.filter(mime_type="video/mp4",res="360p").first()
  stream.download(output_path=download_folder, filename=download_name+".mp4")

  print("averaging colours...")
  if mode == "classic":
    colour_list = get_colour_list(download_folder, download_name, frame_folder)
    print("writing image...")
    output_image = Image.new('RGB', (len(colour_list), len(colour_list)), color = 'white')
    d = ImageDraw.Draw(output_image)
    for index, value in enumerate(colour_list):
      d.line((index,len(colour_list), index, 0), fill=(int(value[0]),int(value[1]),int(value[2])))
    output_image = output_image.resize(resolution,resample=Image.BILINEAR)
  else:
    means = get_frame_means(download_folder+"/"+download_name+".mp4")
    bar_width, bar_height = resolution
    n_bars = 1 if mode == "strip" else pick_bar_count(len(means), bar_width)
    print("writing image (%d frames, %d bar(s))..." % (len(means), n_bars))
    columns = resample_means(means, n_bars * bar_width)
    output_image = render_bars(columns, n_bars, bar_width, bar_height)

  output_image.save(output_file)
  if show:
    output_image.show()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Creates an image of average frame colours for a YouTube video.")
  parser.add_argument("url", nargs="?", help="YouTube video URL (prompts if omitted)")
  parser.add_argument("-m", "--mode", choices=["classic", "strip", "multi"], default="classic",
                      help="classic: one colour per second of video; strip: a single bar built from "
                           "all frames; multi: all frames spread over up to 6 stacked bars (default: classic)")
  parser.add_argument("-r", "--resolution", type=parse_resolution, default=None,
                      help="output image resolution as WIDTHxHEIGHT; in strip/multi modes this is the "
                           "size of a single bar (default: 1920x1080, strip/multi 1920x180)")
  parser.add_argument("-o", "--output", default="output.png",
                      help="output image file name; extension sets the format (default: output.png)")
  parser.add_argument("-n", "--no-show", action="store_true",
                      help="don't open the image after saving")
  args = parser.parse_args()
  if args.resolution is None:
    args.resolution = (1920, 1080) if args.mode == "classic" else (1920, 180)
  video_url = args.url if args.url else input("Enter a YouTube video URL:")
  average_colours(video_url, args.mode, args.resolution, args.output, not args.no_show)
