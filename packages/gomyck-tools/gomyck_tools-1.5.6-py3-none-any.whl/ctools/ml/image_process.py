import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def preprocess(img, img_size):
  mean = [0.485, 0.456, 0.406]
  std = [0.229, 0.224, 0.225]
  img = resize(img, img_size)
  img = img[:, :, ::-1].astype('float32')  # RGB->BGR
  img = normalize(img, mean, std)
  img = img.transpose((2, 0, 1))  # hwc -> chw
  #show_preprocess(img, mean, std)
  return img[np.newaxis, :]


def resize(img, target_size):
  """
  img: numpy.ndarray (H,W,3) BGR or RGB
  return: numpy.ndarray (target_size, target_size, 3)
  """
  img = Image.fromarray(img)
  img = img.resize((target_size, target_size), Image.BILINEAR)
  return np.array(img)


def normalize(img, mean, std):
  img = img / 255.0
  mean = np.array(mean)[np.newaxis, np.newaxis, :]
  std = np.array(std)[np.newaxis, np.newaxis, :]
  img -= mean
  img /= std
  return img


def show_preprocess(chw_img, mean, std):
  """
  chw_img: (3, H, W), float32, normalized
  """
  img = chw_img.copy()
  # 1. CHW -> HWC
  img = img.transpose(1, 2, 0)
  # 2. de-normalize
  img = img * std + mean
  img = img * 255.0
  # 3. clamp + uint8
  img = np.clip(img, 0, 255).astype(np.uint8)
  Image.fromarray(img).show()


def draw_bbox(img, result, threshold=0.5, save_name='res.jpg', scale_factor=None, im_size=320, class_names=None):
  draw = ImageDraw.Draw(img)

  if scale_factor is not None:
    h_scale, w_scale = scale_factor[0]
  else:
    h_scale = w_scale = 1.

  # 类别颜色随机但固定
  category_colors = {}
  if class_names is not None:
    for cls in class_names:
      category_colors[cls] = tuple(random.randint(0, 255) for _ in range(3))

  # 字体
  try:
    font = ImageFont.truetype("arial.ttf", 15)
  except:
    font = ImageFont.load_default()

  for res in result:
    cat_id, score, bbox = res[0], res[1], res[2:]
    if score < threshold:
      continue

    # 归一化 bbox -> 模型输入尺寸
    xmin = bbox[0] * im_size
    ymin = bbox[1] * im_size
    xmax = bbox[2] * im_size
    ymax = bbox[3] * im_size

    # 模型输入尺寸 -> 原图
    xmin = xmin / w_scale
    xmax = xmax / w_scale
    ymin = ymin / h_scale
    ymax = ymax / h_scale

    # 类别名和颜色
    if class_names is not None:
      class_name = class_names[int(cat_id)]
      color = category_colors[class_name]
      text = f"{class_name}:{score:.2f}"

      # 获取文字尺寸，兼容所有版本 Pillow
      try:
        text_width, text_height = font.getsize(text)  # 旧版 / 大部分版本
      except AttributeError:
        # Pillow 9.2+ 推荐用 getbbox
        bbox_font = font.getbbox(text)
        text_width = bbox_font[2] - bbox_font[0]
        text_height = bbox_font[3] - bbox_font[1]

      text_origin = (xmin, max(0, ymin - text_height))  # 框上方显示
      draw.text(text_origin, text, fill=color, font=font)
    else:
      color = 'red'

    # 画矩形框
    draw.rectangle([xmin, ymin, xmax, ymax], outline=color, width=2)

  img.save(save_name)


def image_show(base64_str):
  """base64字符串转PIL Image并显示"""
  from io import BytesIO
  import base64
  img_data = base64.b64decode(base64_str)
  img = Image.open(BytesIO(img_data))
  img.show()
