class ModelConfig:

    def __init__(self, points_per_side, pred_iou_thresh, 
                 stability_score_thresh, 
                 crop_n_layers, 
                 crop_n_points_downscale_factor,min_mask_region_area):
        self.points_per_side = points_per_side
        self.pred_iou_thresh = pred_iou_thresh
        self.stability_score_thresh = stability_score_thresh
        self.crop_n_layers = crop_n_layers
        self.crop_n_points_downscale_factor = crop_n_points_downscale_factor
        self.min_mask_region_area =  min_mask_region_area