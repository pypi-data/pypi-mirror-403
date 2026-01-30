from io import BytesIO
from queue import Queue

import numpy as np
import yaml
from PIL import Image
from paddle.inference import Config, create_predictor

from ctools import path_info
from ctools.ml.image_process import preprocess
from ctools.ml.img_extractor import ClassRegionBase64ExtractorPIL


class PaddlePredictorPool:
  """Predictor 池，用于多线程安全推理"""
  def __init__(self, config_path, pool_size: int = 4):
    """
    初始化预测器池
    Note: 每个 Config 对象只能创建一个 predictor，所以我们需要保存 config_path
    """
    self.config_path = config_path
    self.pool = Queue()
    self._init_pool(pool_size)

  def _load_config_yaml(self):
    """加载 yaml 配置"""
    with open(self.config_path, "r", encoding="utf-8") as f:
      return yaml.safe_load(f)

  def _create_config(self):
    """为新的 predictor 创建一个新的 Config 对象"""
    cfg = self._load_config_yaml()
    model_dir = cfg.get("MODEL_DIR", "")
    model_file = cfg.get("MODEL_FILE", "")
    if not model_file:
      model_dir = path_info.get_app_path('mod/model.pdmodel')
    params_file = cfg.get("PARAMS_FILE", "")
    if not params_file:
      model_dir = path_info.get_app_path('mod/model.pdiparams')
    use_gpu = cfg.get("USE_GPU", False)

    if model_dir:
      config = Config(model_dir)
    else:
      config = Config(model_file, params_file)

    config.enable_memory_optim()

    if use_gpu:
      config.enable_use_gpu(1000, 0)
    else:
      config.set_cpu_math_library_num_threads(4)
      config.enable_mkldnn()

    return config

  def _init_pool(self, pool_size: int):
    """初始化池中的所有 predictor"""
    for _ in range(pool_size):
      config = self._create_config()
      predictor = create_predictor(config)
      self.pool.put(predictor)

  def acquire(self, timeout=None):
    """从池中获取一个 predictor"""
    return self.pool.get(timeout=timeout)

  def release(self, predictor):
    """将 predictor 放回池中"""
    self.pool.put(predictor)


class PaddleInferenceEngine:
  def __init__(self, config_path, pool_size=4):
    self.config_path = config_path
    self.cfg = self._load_config(config_path)
    self.predictor_pool = PaddlePredictorPool(config_path, pool_size=pool_size)

  def _load_config(self, config_path):
    with open(config_path, "r", encoding="utf-8") as f:
      return yaml.safe_load(f)

  def predict(self, inputs, timeout=None):
    """线程安全预测"""
    predictor = self.predictor_pool.acquire(timeout=timeout)
    try:
      input_names = predictor.get_input_names()
      for name in input_names:
        if name not in inputs:
          raise ValueError(f"缺少模型输入: {name}")
        tensor = predictor.get_input_handle(name)
        data = inputs[name]
        tensor.reshape(data.shape)
        tensor.copy_from_cpu(data)
      predictor.run()
      outputs = []
      for name in predictor.get_output_names():
        out = predictor.get_output_handle(name)
        outputs.append(out.copy_to_cpu())
      return outputs
    finally:
      self.predictor_pool.release(predictor)

  def predict_image(self, img, im_size=320):
    if isinstance(img, bytes):
      img = Image.open(BytesIO(img)).convert("RGB")
    elif isinstance(img, Image.Image):
      img = img.convert("RGB")
    elif isinstance(img, np.ndarray):
      pass
    else:
      raise ValueError("Unsupported image type for predict_image")
    orig_img_np = np.array(img) if not isinstance(img, np.ndarray) else img
    data = preprocess(orig_img_np, im_size)
    scale_factor = np.array([im_size * 1. / orig_img_np.shape[0], im_size * 1. / orig_img_np.shape[1]]).reshape((1, 2)).astype(np.float32)
    im_shape = np.array([im_size, im_size]).reshape((1, 2)).astype(np.float32)
    outputs = self.predict({"image": data, "im_shape": im_shape, "scale_factor": scale_factor})
    return outputs, scale_factor, im_size

  def predict_image_and_extract(self, img, im_size=320, class_names=None, target_classes=None, threshold=0.3):
    """预测并提取检测区域"""
    raw_outputs, scale_factor, im_size_ret = self.predict_image(img, im_size=im_size)

    # 转换为 PIL Image
    if isinstance(img, bytes):
      pil_img = Image.open(BytesIO(img)).convert("RGB")
    elif isinstance(img, Image.Image):
      pil_img = img.convert("RGB")
    elif isinstance(img, np.ndarray):
      pil_img = Image.fromarray(img.astype('uint8')).convert("RGB")
    else:
      raise ValueError("Unsupported image type")

    # 提取检测区域
    extractor = ClassRegionBase64ExtractorPIL(class_names or [], target_classes=target_classes, threshold=threshold)
    detection_results = raw_outputs[0]
    return extractor.extract(pil_img, detection_results, scale_factor=scale_factor, im_size=im_size_ret)

  @staticmethod
  def _nms_detections(detections, iou_threshold=0.5):
    if len(detections) == 0:
      return detections
    dets = np.array(detections, dtype=np.float32)
    scores = dets[:, 1]
    sorted_idx = np.argsort(-scores)
    keep = []
    while len(sorted_idx) > 0:
      current_idx = sorted_idx[0]
      keep.append(current_idx)
      if len(sorted_idx) == 1:
        break
      current_box = dets[current_idx, 2:6]
      other_boxes = dets[sorted_idx[1:], 2:6]
      x1_inter = np.maximum(current_box[0], other_boxes[:, 0])
      y1_inter = np.maximum(current_box[1], other_boxes[:, 1])
      x2_inter = np.minimum(current_box[2], other_boxes[:, 2])
      y2_inter = np.minimum(current_box[3], other_boxes[:, 3])
      inter_area = np.maximum(0, x2_inter - x1_inter) * np.maximum(0, y2_inter - y1_inter)
      area_current = (current_box[2] - current_box[0]) * (current_box[3] - current_box[1])
      area_others = (other_boxes[:, 2] - other_boxes[:, 0]) * (other_boxes[:, 3] - other_boxes[:, 1])
      union_area = area_current + area_others - inter_area
      iou = inter_area / (union_area + 1e-6)
      valid_idx = np.where(iou < iou_threshold)[0] + 1
      sorted_idx = sorted_idx[valid_idx]
    return dets[keep].tolist()

  def predict_image_tiled(self, img, im_size=320, tile_overlap=0.2, class_names=None, target_classes=None, threshold=0.3, nms_iou=0.5):
    """
    Tiled prediction for large images (2K, 4K, etc).
    Splits image into overlapping tiles, predicts each tile, merges results.

    Args:
      img: PIL Image, numpy array, or bytes
      im_size: model training resolution (e.g., 320)
      tile_overlap: overlap ratio between tiles (0.0-1.0), default 0.2
      class_names: list of class names
      target_classes: list of target classes to extract
      threshold: confidence threshold
      nms_iou: IoU threshold for NMS merging

    Returns:
      extracted_outputs: list of dicts with extracted regions (with coordinates mapped to original image)
      all_detections: list of raw detections [cat_id, score, xmin, ymin, xmax, ymax] (original image coords)
    """
    # Convert input to numpy array
    if isinstance(img, bytes):
      pil_img = Image.open(BytesIO(img)).convert("RGB")
      img_np = np.array(pil_img)
    elif isinstance(img, Image.Image):
      img_np = np.array(img.convert("RGB"))
    elif isinstance(img, np.ndarray):
      img_np = img
    else:
      raise ValueError("Unsupported image type for predict_image_tiled")
    orig_h, orig_w = img_np.shape[:2]
    # Calculate tile parameters
    stride = int(im_size * (1 - tile_overlap))
    stride = max(1, stride)
    # Generate tile coordinates
    tiles = []
    y_start = 0
    while y_start < orig_h:
      y_end = min(y_start + im_size, orig_h)
      # If last tile doesn't cover the bottom, adjust
      if y_end == orig_h and y_start > 0:
        y_start = max(0, orig_h - im_size)
        y_end = orig_h
      x_start = 0
      while x_start < orig_w:
        x_end = min(x_start + im_size, orig_w)
        # If last tile doesn't cover the right, adjust
        if x_end == orig_w and x_start > 0:
          x_start = max(0, orig_w - im_size)
          x_end = orig_w
        tiles.append((x_start, y_start, x_end, y_end))
        x_start += stride
        if x_end == orig_w:
          break
      y_start += stride
      if y_end == orig_h:
        break
    # Predict each tile and collect detections
    all_detections = []
    for x_start, y_start, x_end, y_end in tiles:
      tile_img = img_np[y_start:y_end, x_start:x_end]
      # Pad tile if smaller than im_size
      if tile_img.shape[0] < im_size or tile_img.shape[1] < im_size:
        pad_h = im_size - tile_img.shape[0]
        pad_w = im_size - tile_img.shape[1]
        tile_img = np.pad(tile_img, ((0, pad_h), (0, pad_w), (0, 0)), mode='constant', constant_values=0)
      # Run inference on tile
      try:
        tile_outputs, _, _ = self.predict_image(tile_img, im_size=im_size)
        tile_detections = tile_outputs[0]
        # Map coordinates back to original image
        for det in tile_detections:
          cat_id, score = det[0], det[1]
          xmin, ymin, xmax, ymax = det[2], det[3], det[4], det[5]
          # Scale from model resolution to tile resolution
          tile_h, tile_w = y_end - y_start, x_end - x_start
          xmin_tile = xmin * tile_w / im_size
          ymin_tile = ymin * tile_h / im_size
          xmax_tile = xmax * tile_w / im_size
          ymax_tile = ymax * tile_h / im_size
          # Translate to original image coordinates
          xmin_orig = xmin_tile + x_start
          ymin_orig = ymin_tile + y_start
          xmax_orig = xmax_tile + x_start
          ymax_orig = ymax_tile + y_start
          # Clip to image bounds
          xmin_orig = max(0, min(xmin_orig, orig_w))
          ymin_orig = max(0, min(ymin_orig, orig_h))
          xmax_orig = max(0, min(xmax_orig, orig_w))
          ymax_orig = max(0, min(ymax_orig, orig_h))
          all_detections.append([cat_id, score, xmin_orig, ymin_orig, xmax_orig, ymax_orig])
      except Exception as e:
        print(f"Error processing tile {(x_start, y_start, x_end, y_end)}: {e}")
        continue
    # Apply NMS to merge duplicate detections
    merged_detections = self._nms_detections(all_detections, iou_threshold=nms_iou)

    # Extract regions using the merged detections
    if isinstance(img, bytes):
      pil_img = Image.open(BytesIO(img)).convert("RGB")
    elif isinstance(img, Image.Image):
      pil_img = img.convert("RGB")
    elif isinstance(img, np.ndarray):
      pil_img = Image.fromarray(img_np.astype('uint8')).convert("RGB")
    else:
      raise ValueError("Unsupported image type")

    # Create a dummy scale_factor (1:1 since we're already in original coordinates)
    scale_factor = np.array([[1.0, 1.0]], dtype=np.float32)
    extractor = ClassRegionBase64ExtractorPIL(class_names or [], target_classes=target_classes, threshold=threshold)
    extracted = extractor.extract(pil_img, merged_detections, scale_factor=scale_factor, im_size=orig_h)
    return extracted, merged_detections
