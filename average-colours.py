#pip install list:
# pytubefix
# opencv-python
# pillow

from pytubefix import YouTube
import argparse
import cv2
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

def parse_resolution(value):
  try:
    width, height = value.lower().split("x")
    return (int(width), int(height))
  except ValueError:
    raise argparse.ArgumentTypeError("resolution must be WIDTHxHEIGHT, e.g. 1920x1080")

def average_colours(video_url, resolution=(1920, 1080), output_file="output.png"):
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
  colour_list = get_colour_list(download_folder, download_name, frame_folder)

  print("writing image...")
  output_image = Image.new('RGB', (len(colour_list), len(colour_list)), color = 'white')
  d = ImageDraw.Draw(output_image)

  for index, value in enumerate(colour_list):
    d.line((index,len(colour_list), index, 0), fill=(int(value[0]),int(value[1]),int(value[2])))
  
  output_image = output_image.resize(resolution,resample=Image.BILINEAR)
  output_image.save(output_file)
  output_image.show()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Creates an image of average frame colours for a YouTube video.")
  parser.add_argument("url", nargs="?", help="YouTube video URL (prompts if omitted)")
  parser.add_argument("-r", "--resolution", type=parse_resolution, default=(1920, 1080),
                      help="output image resolution as WIDTHxHEIGHT (default: 1920x1080)")
  parser.add_argument("-o", "--output", default="output.png",
                      help="output image file name; extension sets the format (default: output.png)")
  args = parser.parse_args()
  video_url = args.url if args.url else input("Enter a YouTube video URL:")
  average_colours(video_url, args.resolution, args.output)
