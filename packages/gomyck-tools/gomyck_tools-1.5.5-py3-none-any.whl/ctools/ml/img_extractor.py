#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = 'haoyang'
__date__ = '2026/1/20 15:02'

import base64
from io import BytesIO

class ClassRegionBase64ExtractorPIL:
  def __init__(self, class_names, target_classes=None, threshold=0.5):
    """
    class_names: 模型类别列表
    target_classes: 只截取的类别名列表，None 表示全部
    threshold: 置信度阈值
    """
    self.class_names = class_names
    self.target_classes = target_classes
    self.threshold = threshold

  @staticmethod
  def image_to_base64(img, format='PNG'):
    """
    PIL Image -> base64 字符串
    """
    buffer = BytesIO()
    img.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

  def extract(self, img, results, scale_factor=None, im_size=320):
    """
    img: PIL Image
    results: 模型输出 [[cat_id, score, xmin, ymin, xmax, ymax], ...]
    scale_factor: np.array([[h_scale, w_scale]]) 或 None
    im_size: 模型输入尺寸
    return: List[Dict] -> [{"class": class_name, "score": score, "base64": base64_str}, ...]
    """
    outputs = []
    for res in results:
      cat_id, score, bbox = res[0], res[1], res[2:]
      if score < self.threshold or cat_id > len(self.class_names) - 1:
        continue
      class_name = self.class_names[int(cat_id)]
      if self.target_classes is not None and class_name not in self.target_classes:
        continue
      xmin = bbox[0]
      ymin = bbox[1]
      xmax = bbox[2]
      ymax = bbox[3]
      # 裁剪
      pil_img_threadsafe = img.copy()
      cropped = pil_img_threadsafe.crop((xmin, ymin, xmax, ymax))
      # 转 base64
      b64_str = self.image_to_base64(cropped)
      outputs.append({
        "class": class_name,
        "score": float(score),
        "base64": b64_str
      })
    return outputs
